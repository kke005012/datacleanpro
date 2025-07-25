import pandas as pd
import numpy as np
import re
from dateutil import parser

# --- cleaner.py ---

verbose = False 

def clean_data(df, keep_dollar=False, ):
    if logger is None:
        logger = lambda *args, **kwargs: None  # no-op if not passed

    log_lines = []

    # 1. Strip whitespace
    df, strip_log = strip_whitespace(df, verbose=verbose)
    log_lines.extend(strip_log)
    logger("##DEBUG: After strip_whitespace:", df.head())

    # 2. Drop empty rows
    df, drop_log = drop_empty_rows(df, verbose=verbose)
    log_lines.extend(drop_log)
    logger("##DEBUG: After drop_empty_rows:", df.head())

    # 3. Deduplicate
    df, dedup_log = deduplicate(df, verbose=verbose)
    log_lines.extend(dedup_log)
    logger("##DEBUG: After deduplicate:", df.head())

    # 4. Standardize column names
    df, colname_log = standardize_column_names(df, verbose=verbose)
    log_lines.extend(colname_log)
    logger("##DEBUG: After standardize_column_names:", df.head())

    # 5. Clean currency columns
    df, currency_log = clean_currency_columns(df, keep_dollar=keep_dollar, verbose=verbose, missing_values_option=missing_values_option)
    log_lines.extend(currency_log)
    logger("##DEBUG: After clean_currency_columns:", df.head())

    # 6. Normalize date columns
    df, date_log = normalize_dates(df, verbose=verbose)
    log_lines.extend(date_log)
    logger("##DEBUG: After normalize_dates:", df.head())

    # 7. Handle missing values
    df, missing_log = handle_missing_values(df, numeric_strategy, non_numeric_strategy, num_missing_placeholder=num_missing_placeholder,
        non_num_missing_placeholder=non_num_missing_placeholder, missing_values_option=missing_values_option, verbose=verbose)
    log_lines.extend(missing_log)
    logger("##DEBUG: After handle_missing_values:", df.head())

    # 8. (Optional) Final sanity check
    # df = final_sanity_check(df)
    # log_lines.append("Performed final sanity checks")

    # Attach log and logger for export or UI display
    df.attrs["log"] = log_lines
    df.attrs["logger"] = logger

    return df


def strip_whitespace(df, verbose=verbose):
    log = []
    changed_cols = []

    for col in df.columns:
        if df[col].dtype == object:
            original = df[col].copy()
            df[col] = df[col].astype(str).str.strip()
            if not original.equals(df[col]):
                changed_cols.append(col)

    if changed_cols:
        log.append(f"Stripped whitespace in {len(changed_cols)} column(s): {', '.join(changed_cols)}.")
    elif verbose:
        log.append("No whitespace stripping needed.")

    return df, log


def drop_empty_rows(df, verbose=verbose):
    log = []
    original_len = len(df)
    df = df.dropna(axis=0, how='all')
    dropped = original_len - len(df)

    if dropped > 0:
        log.append(f"Dropped {dropped} completely empty row(s).")
    elif verbose:
        log.append("No completely empty rows found.")

    return df, log


def deduplicate(df, verbose=verbose):
    log = []
    original_len = len(df)
    df = df.drop_duplicates()
    removed = original_len - len(df)

    if removed > 0:
        log.append(f"Removed {removed} duplicate row(s).")
    elif verbose:
        log.append("No duplicate rows found.")

    return df, log


def standardize_column_names(df, verbose=verbose):
    log = []
    original_columns = df.columns.tolist()
    cleaned_columns = []

    for col in original_columns:
        new_col = col.strip().lower()
        new_col = re.sub(r'[^\w\s]', '', new_col)     # remove special chars
        new_col = re.sub(r'\s+', '_', new_col)        # replace whitespace with underscore
        cleaned_columns.append(new_col)

    df.columns = cleaned_columns

    if original_columns != cleaned_columns:
        renamed_pairs = [
            f"'{orig}' → '{new}'" for orig, new in zip(original_columns, cleaned_columns) if orig != new
        ]
        log.append(f"Standardized column names: {', '.join(renamed_pairs)}.")
    elif verbose:
        log.append("No changes to column names.")
    

    return df, log


def clean_currency_columns(df, keep_dollar=False, verbose=False):
    log = []

    for col in df.columns:
        if df[col].dtype == object:
            if df[col].str.contains(r'\$|,|_', na=False).any():
                original_non_null = df[col].notna().sum()

                # Remove $, , and _
                df[col] = df[col].replace(r'[\$,]', '', regex=True)
                df[col] = df[col].replace(r'_', '', regex=True)

                # Convert to float
                df[col] = pd.to_numeric(df[col], errors='coerce')

                cleaned_non_null = df[col].notna().sum()

                if cleaned_non_null > 0:
                    # Format to 2 decimal places and replace missing
                    if missing_values_option != "":
                        df[col] = df[col].apply(
                            lambda x: missing_values_option if pd.isna(x) else f"{x:.2f}"
                        )
                    else:
                        df[col] = df[col].apply(
                            lambda x: f"{x:.2f}" if pd.notna(x) else np.nan
                        )

                    # Optional: re-add dollar sign
                    if keep_dollar:
                        df[col] = df[col].apply(
                            lambda x: f"${x}" if pd.notna(x) and not str(x).startswith("$") and str(x) != str(missing_values_option) else x
                        )

                    # Ensure consistent type
                    df[col] = df[col].astype(str)

                    log.append(f"💵 Cleaned and standardized {cleaned_non_null} currency values in '{col}'")
                else:
                    log.append(f"⚠️ Currency format found in '{col}', but no values were successfully converted")
            elif verbose:
                log.append(f"✅ Column '{col}' had no currency formatting")

    if not log and verbose:
        log.append("✅ No currency formats detected in any column")

    return df, log


def is_likely_date(val):
    if not isinstance(val, str):
        return False
    date_patterns = [
        r"\d{4}[-/]\d{2}[-/]\d{2}",     # YYYY-MM-DD or YYYY/MM/DD
        r"\d{2}[-/]\d{2}[-/]\d{4}",     # MM-DD-YYYY or DD-MM-YYYY
        r"[A-Za-z]{3,9} \d{1,2}, \d{4}" # Month DD, YYYY
    ]
    return any(re.search(pat, val) for pat in date_patterns)

def normalize_dates(df, verbose=verbose):
    log = []

    for col in df.columns:
        if df[col].dtype == object:
            # Only try parsing if the sample data looks like dates
            sample = df[col].dropna().astype(str).head(10).tolist()
            if not any(is_likely_date(val) for val in sample):
                if verbose:
                    log.append(f"ℹ️ Skipped '{col}': no date-like patterns found.")
                continue

            original_non_null = df[col].notna().sum()
            try:
                parsed = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
                parsed_non_null = parsed.notna().sum()

                if parsed_non_null > 0:
                    df[col] = parsed
                    log.append(f"📅 Parsed {parsed_non_null} date values in '{col}' to standardized format (YYYY-MM-DD).")
                elif verbose:
                    log.append(f"ℹ️ Attempted to parse '{col}', but no valid dates found.")
            except Exception as e:
                log.append(f"⚠️ Failed to parse '{col}' due to error: {str(e)}")

    if not log and verbose:
        log.append("ℹ️ No columns parsed as dates")

    return df, log


def handle_missing_values(df, numeric_strategy, non_numeric_strategy):
    log = []

    for col in df.columns:
        if df[col].isnull().any() or (df[col] == "").any():
            if pd.api.types.is_numeric_dtype(df[col]):
                if numeric_strategy == "Unknown":
                    df[col] = df[col].fillna("Unknown")
                    log.append(f"Filled missing numeric values in '{col}' with 'Unknown'")
                elif numeric_strategy == "Average/Mode":
                    mean_val = df[col].mean()
                    df[col] = df[col].fillna(mean_val)
                    log.append(f"Filled missing numeric values in '{col}' with mean ({mean_val:.2f})")
                elif numeric_strategy == "Ignore":
                    log.append(f"Ignored missing values in numeric column '{col}'")
            else:
                if non_numeric_strategy == "Unknown":
                    df[col] = df[col].replace(["", None, pd.NA, np.nan], "Unknown")
                    log.append(f"Filled missing non-numeric values in '{col}' with 'Unknown'")
                elif non_numeric_strategy == "Average/Mode":
                    mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown"
                    df[col] = df[col].fillna(mode_val).replace("", mode_val)
                    log.append(f"Filled missing non-numeric values in '{col}' with mode ('{mode_val}')")
                elif non_numeric_strategy == "Ignore":
                    log.append(f"Ignored missing values in non-numeric column '{col}'")
    
    return df, log

def write_log(cleaned_df):
    return cleaned_df.attrs.get("log", ["No cleaning log available."])

#def final_sanity_check(df):
    #possibly add functionality later if customer wants to drop columns where all values are missing