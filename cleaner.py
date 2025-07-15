# --- cleaner.py ---
def clean_data(df, handle_missing=False):
    log_lines = []

    # 1. Strip whitespace
    df = strip_whitespace(df)
    log_lines.append(f"✔️ Stripped leading/trailing whitespace")

    # 2. Drop empty rows
    original_len = len(df)
    df = drop_empty_rows(df)
    log_lines.append(f"✔️ Dropped {original_len - len(df)} completely empty rows")

    # 3. Deduplicate
    before_dedup = len(df)
    df = deduplicate(df)
    log_lines.append(f"✔️ Removed {before_dedup - len(df)} duplicate rows")

    # 4. Standardize column names
    df = standardize_column_names(df)
    log_lines.append(f"✔️ Standardized column names")

    # 5. Normalize currency and date columns
    df = clean_currency_columns(df)
    df = normalize_dates(df)
    log_lines.append(f"✔️ Normalized currency and date formats")

    # 6. Handle missing values (if selected)
    if handle_missing:
        df = handle_missing_values(df)
        log_lines.append(f"✔️ Filled missing values")

    # 7. Final sanity check
    df = final_sanity_check(df)
    log_lines.append(f"✔️ Performed final sanity checks")

    df.attrs['log'] = log_lines
    return df


def strip_whitespace(df):
    return df.applymap(lambda x: x.strip() if isinstance(x, str) else x)


def drop_empty_rows(df):
    return df.dropna(how='all')


def deduplicate(df):
    return df.drop_duplicates()


def write_log(original_df, cleaned_df):
    return cleaned_df.attrs.get('log', ["No log information available."])


def standardize_column_names(df):
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    return df


def clean_currency_columns(df):
    for col in df.columns:
        if df[col].dtype == object and df[col].str.contains("$").any():
            df[col] = df[col].replace('[\$,]', '', regex=True).astype(float)
    return df


def normalize_dates(df):
    for col in df.columns:
        if df[col].dtype == object:
            try:
                df[col] = pd.to_datetime(df[col], errors='ignore')
            except Exception:
                continue
    return df


def handle_missing_values(df):
    return df.fillna("[Missing]")


def final_sanity_check(df):
    return df.dropna(axis=1, how='all')
