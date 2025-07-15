import pandas as pd

# --- cleaner.py ---

def clean_data(df, numeric_strategy="ignore", non_numeric_strategy="ignore"):
    log_lines = []

    # 1. Strip whitespace
    df = strip_whitespace(df)
    log_lines.append(f"Stripped leading/trailing whitespace")

    # 2. Drop empty rows
    original_len = len(df)
    df = drop_empty_rows(df)
    log_lines.append(f"Dropped {original_len - len(df)} completely empty rows")

    # 3. Deduplicate
    before_dedup = len(df)
    df = deduplicate(df)
    log_lines.append(f"Removed {before_dedup - len(df)} duplicate rows")

    # 4. Standardize column names
    df = standardize_column_names(df)
    log_lines.append(f"Standardized column names")

    # 5. Normalize currency and date columns
    df = clean_currency_columns(df)
    df = normalize_dates(df)
    log_lines.append(f"Normalized currency and date formats")

    # 6. Handle missing values (based on strategy)
    df = handle_missing_values(df, numeric_strategy, non_numeric_strategy, log_lines)

    # 7. Final sanity check
    df = final_sanity_check(df)
    log_lines.append(f"Performed final sanity checks")

    df.attrs['log'] = log_lines
    return df


def strip_whitespace(df):
    for col in df.select_dtypes(include='object'):
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)
    return df

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
    import re
    for col in df.columns:
        if df[col].dtype == object and df[col].str.contains("\\$").any():
            cleaned = df[col].replace('[\\$,]', '', regex=True)
            df[col] = cleaned.apply(lambda x: float(x) if re.fullmatch(r"-?\d+(\.\d+)?", str(x).strip()) else x)
    return df


def normalize_dates(df):
    for col in df.columns:
        if df[col].dtype == object:
            try:
                df[col] = pd.to_datetime(df[col], format="%Y-%m-%d", errors='coerce')
            except Exception:
                continue
    return df


def handle_missing_values(df, numeric_strategy, non_numeric_strategy, log_lines):
    for col in df.columns:
        if df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                if numeric_strategy == "unknown":
                    df[col] = df[col].fillna("Unknown")
                    log_lines.append(f"⚠️ Filled numeric column '{col}' with 'Unknown'")
                elif numeric_strategy == "average":
                    df[col] = df[col].fillna(df[col].mean())
                    log_lines.append(f"Filled numeric column '{col}' with average")
                else:
                    log_lines.append(f"Numeric column '{col}' left unchanged (ignored)")
            else:
                if non_numeric_strategy == "unknown":
                    df[col] = df[col].fillna("Unknown")
                    log_lines.append(f"Filled non-numeric column '{col}' with 'Unknown'")
                elif non_numeric_strategy == "mode":
                    mode = df[col].mode()
                    if not mode.empty:
                        df[col] = df[col].fillna(mode[0])
                        log_lines.append(f"Filled non-numeric column '{col}' with mode value '{mode[0]}'")
                else:
                    log_lines.append(f"Non-numeric column '{col}' left unchanged (ignored)")
    return df


def final_sanity_check(df):
    return df.dropna(axis=1, how='all')