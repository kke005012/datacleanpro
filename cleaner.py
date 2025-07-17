import pandas as pd
import numpy as np

# --- cleaner.py ---

def clean_data(df, numeric_strategy="ignore", non_numeric_strategy="ignore", logger=None):
    if logger is None:
        logger = lambda *args, **kwargs: None  # no-op if not passed
    
    log_lines = []

    # 1. Strip whitespace
    df = strip_whitespace(df)
    log_lines.append(f"Stripped leading/trailing whitespace")
    logger(f"##DEBUG 1: After strip_whitespace:", df.shape)

    # 2. Drop empty rows
    original_len = len(df)
    df = drop_empty_rows(df)
    log_lines.append(f"Dropped {original_len - len(df)} completely empty rows")
    logger(f"##DEBUG 2: After replace blank rows with NaN:", df.shape)

    # 3. Deduplicate
    before_dedup = len(df)
    df = deduplicate(df)
    log_lines.append(f"Removed {before_dedup - len(df)} duplicate rows")
    logger(f"##DEBUG 3: After deduplicate:", df.shape)

    # 4. Standardize column names
    df = standardize_column_names(df)
    log_lines.append(f"Standardized column names")
    logger(f"##DEBUG 4: After standardize_column_names:", df.shape)

    # 5. Normalize currency and date columns
    df = clean_currency_columns(df)
    df = normalize_dates(df)
    log_lines.append(f"Normalized currency and date formats")
    logger(f"##DEBUG 5: After clean_currency_columns and normalize dates:", df.shape)

    # 6. Handle missing values (based on strategy)
    df = handle_missing_values(df, numeric_strategy, non_numeric_strategy, log_lines)
    log_lines.append(f"Handled Missing Values")
    logger(f"DEBUG 6: After handle_missing_values:", df.shape)

    # 7. Final sanity check
    #df = final_sanity_check(df)
    #log_lines.append(f"Performed final sanity checks")

    df.attrs['log'] = log_lines
    df.attrs['logger'] = logger
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
    return cleaned_df.attrs.get('log', ["No cleaning log available."])


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
        is_numeric = pd.api.types.is_numeric_dtype(df[col])
        has_nulls = df[col].isnull().any()
        has_empty = (df[col] == "").any() if not is_numeric else False

        if has_nulls or has_empty:
            if is_numeric:
                if numeric_strategy == "unknown":
                    num_missing = df[col].isnull().sum()
                    df[col] = df[col].fillna(-1)
                    log_lines.append(f"⚠️ Filled {num_missing} missing values in numeric column '{col}' with -1")
                elif numeric_strategy == "average":
                    num_missing = df[col].isnull().sum()
                    df[col] = df[col].fillna(df[col].mean())
                    log_lines.append(f"Filled {num_missing} missing values in numeric column '{col}' with average")
                else:
                    log_lines.append(f"Numeric column '{col}' left unchanged (ignored)")
            else:
                if non_numeric_strategy == "unknown":
                    # Count how many were replaced (either NaN or empty strings)
                    num_missing = df[col].apply(lambda x: pd.isna(x) or x == "").sum()
                    df[col] = df[col].apply(lambda x: "Unknown" if (pd.isna(x) or (isinstance(x, str) and x.strip() == "")) else x)
                    log_lines.append(f"⚠️ Filled {num_missing} missing values in non-numeric column '{col}' with 'Unknown'")
                 
                elif non_numeric_strategy == "mode":
                    mode = df[col][df[col] != ""].mode()
                    if not mode.empty:
                        df[col] = df[col].replace("", np.nan)
                        num_missing = df[col].isnull().sum()
                        df[col] = df[col].fillna(mode[0])
                        log_lines.append(f"Filled {num_missing} missing values in non-numeric column '{col}' with mode value '{mode[0]}'")
                else:
                    log_lines.append(f"Non-numeric column '{col}' left unchanged (ignored)")
    return df


#def final_sanity_check(df):
    #possibly add functionality later if customer wants to drop columns where all values are missing
    