import pandas as pd
import numpy as np
import re
from dateutil import parser

# --- cleaner.py ---

verbose = False 

def clean_data(df, keep_dollar=False, numeric_strategy="ignore", non_numeric_strategy="ignore", logger=None):
    if logger is None:
        logger = lambda *args, **kwargs: None  # no-op if not passed

    log_lines = []

    # 1. Strip whitespace
    df, strip_log = strip_whitespace(df, verbose=verbose, logger=logger)
    log_lines.extend(strip_log)
    logger(f"##DEBUG: After strip_whitespace:", df.head())
    for col in ["mas_vnr_type", "bsmt_exposure\r"]:
        if col in df.columns:
            logger(f"##DEBUG [{col}] — nulls: {df[col].isna().sum()} | empties: {(df[col] == '').sum()} | type: {df[col].dtype}")
            logger(df[col].head())
        else:
            logger(f"##DEBUG: Column '{col}' not found after this step.")

    # 2. Drop empty rows
    df, drop_log = drop_empty_rows(df, verbose=verbose, logger=logger)
    log_lines.extend(drop_log)
    logger("##DEBUG: After drop_empty_rows:", df.head())
    for col in ["mas_vnr_type", "bsmt_exposure\r"]:
        if col in df.columns:
            logger(f"##DEBUG [{col}] — nulls: {df[col].isna().sum()} | empties: {(df[col] == '').sum()} | type: {df[col].dtype}")
            logger(df[col].head())
        else:
            logger(f"##DEBUG: Column '{col}' not found after this step.")

    # 3. Deduplicate
    df, dedup_log = deduplicate(df, verbose=verbose, logger=logger)
    log_lines.extend(dedup_log)
    logger("##DEBUG: After deduplicate:", df.head())
    for col in ["mas_vnr_type", "bsmt_exposure\r"]:
        if col in df.columns:
            logger(f"##DEBUG [{col}] — nulls: {df[col].isna().sum()} | empties: {(df[col] == '').sum()} | type: {df[col].dtype}")
            logger(df[col].head())
        else:
            logger(f"##DEBUG: Column '{col}' not found after this step.")

    # 4. Standardize column names
    df, colname_log = standardize_column_names(df, verbose=verbose, logger=logger)
    log_lines.extend(colname_log)
    logger("##DEBUG: After standardize_column_names:", df.head())
    for col in ["mas_vnr_type", "bsmt_exposure\r"]:
        if col in df.columns:
            logger(f"##DEBUG [{col}] — nulls: {df[col].isna().sum()} | empties: {(df[col] == '').sum()} | type: {df[col].dtype}")
            logger(df[col].head())
        else:
            logger(f"##DEBUG: Column '{col}' not found after this step.")

    # 5. Clean currency columns
    df, currency_log = clean_currency_columns(df, keep_dollar=keep_dollar, verbose=verbose)
    log_lines.extend(currency_log)
    logger("##DEBUG: After clean_currency_columns:", df.head())
    for col in ["mas_vnr_type", "bsmt_exposure"]:
        if col in df.columns:
            logger(f"##DEBUG [{col}] — nulls: {df[col].isna().sum()} | empties: {(df[col] == '').sum()} | type: {df[col].dtype}")
            logger(df[col].head())
        else:
            logger(f"##DEBUG: Column '{col}' not found after this step.")

    # 6. Normalize date columns
    df, date_log = normalize_dates(df, verbose=verbose, logger=logger)
    log_lines.extend(date_log)
    logger("##DEBUG: After normalize_dates:", df.head())
    for col in ["mas_vnr_type", "bsmt_exposure"]:
        if col in df.columns:
            logger(f"##DEBUG [{col}] — nulls: {df[col].isna().sum()} | empties: {(df[col] == '').sum()} | type: {df[col].dtype}")
            logger(df[col].head())
        else:
            logger(f"##DEBUG: Column '{col}' not found after this step.")

    # 7. Handle missing values
    df, missing_log = handle_missing_values(df, numeric_strategy, non_numeric_strategy, verbose=verbose, logger=logger)
    log_lines.extend(missing_log)
    logger("##DEBUG: After handle_missing_values:", df.head())
    for col in ["mas_vnr_type", "bsmt_exposure"]:
        if col in df.columns:
            logger(f"##DEBUG [{col}] — nulls: {df[col].isna().sum()} | empties: {(df[col] == '').sum()} | type: {df[col].dtype}")
            logger(df[col].head())
        else:
            logger(f"##DEBUG: Column '{col}' not found after this step.")

    # 8. (Optional) Final sanity check
    # df = final_sanity_check(df)
    # log_lines.append("Performed final sanity checks")

    # Attach log and logger for export or UI display
    df.attrs["log"] = log_lines
    df.attrs["logger"] = logger

    return df

def strip_whitespace(df, verbose=verbose, logger=None):
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


def drop_empty_rows(df, verbose=verbose, logger=None):
    log = []
    original_len = len(df)
    df = df.dropna(axis=0, how='all')
    dropped = original_len - len(df)

    if dropped > 0:
        log.append(f"Dropped {dropped} completely empty row(s).")
    elif verbose:
        log.append("No completely empty rows found.")

    return df, log


def deduplicate(df, verbose=verbose, logger=None):
    log = []
    original_len = len(df)
    df = df.drop_duplicates()
    removed = original_len - len(df)

    if removed > 0:
        log.append(f"Removed {removed} duplicate row(s).")
    elif verbose:
        log.append("No duplicate rows found.")

    return df, log


def standardize_column_names(df, verbose=verbose, logger=None):
    log = []
    original_columns = df.columns.tolist()
    cleaned_columns = []

    for col in original_columns:
        new_col = col.strip().lower()
        new_col = col.strip().lower().replace("\r", "")
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


def clean_currency_columns(df, keep_dollar=False, verbose=False, logger=None):
    log = []

    for col in df.columns:
        # ⛔ Skip date-like or year-like columns
        if 'date' in col.lower() or 'year' in col.lower():
            continue

        if df[col].dtype == object:
            # 🔍 Look for currency indicators
            if df[col].str.contains(r'\$|,|_', na=False).any():
                original_non_null = df[col].notna().sum()

                # 🧼 Strip currency symbols and formatting
                df[col] = df[col].replace(r'[\$,]', '', regex=True)
                df[col] = df[col].replace(r'_', '', regex=True)

                # 🔄 Convert to numeric
                df[col] = pd.to_numeric(df[col], errors='coerce')
                cleaned_non_null = df[col].notna().sum()

                if cleaned_non_null > 0:
                    # 💲 Format as 2-decimal strings
                    df[col] = df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else x)

                    if keep_dollar:
                        df[col] = df[col].apply(
                            lambda x: f"${x}" if pd.notna(x) and not str(x).startswith("$") else x
                        )

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
        val = str(val)

    val = val.strip().lower()

    # Common date substrings (month names, T/Z, slashes, dashes)
    if any(month in val for month in [
        "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "oct", "nov", "dec"
    ]):
        return True

    if "t" in val and "z" in val:  # ISO format like 2025-07-19T14:30Z
        return True

    # Common separators
    if re.match(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", val):  # 19/07/2028
        return True
    if re.match(r"\d{4}[./-]\d{1,2}[./-]\d{1,2}", val):  # 2025.07.18
        return True
    if re.match(r"\d{8}$", val):  # 19680719
        return True
    if re.match(r"\d{1,2}-[a-z]{3}-\d{2,4}", val):  # 23-Jul-25
        return True

    return False


def normalize_dates(df, verbose=False, logger=None):
    log = []

    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_numeric_dtype(df[col]):
            sample = df[col].dropna().astype(str).head(10).tolist()
            if not any(is_likely_date(val) for val in sample):
                if verbose:
                    log.append(f"ℹ️ Skipped '{col}': no date-like patterns found.")
                continue

            try:
                # 🧼 Replace known garbage with NaT
                df[col] = df[col].replace(["NULL", "InvalidDate", "NaT", ""], pd.NaT)

                # 🧽 Clean up string format
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].str.replace(r"[.]", "-", regex=True)
                df[col] = df[col].str.replace(r"\s+", " ", regex=True)

                # Handle UNIX timestamps if column is numeric
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = pd.to_datetime(df[col], unit="s", errors="coerce")
                # Special handling for ISO timestamps
                elif df[col].str.contains("T", na=False).any():
                    df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
                else:
                    df[col] = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True, dayfirst=True)

                parsed_non_null = df[col].notna().sum()
                if parsed_non_null > 0:
                    log.append(f"📅 Parsed {parsed_non_null} date values in '{col}' to standardized format.")
                failed = df[col].isna().sum()
                if failed > 0:
                    log.append(f"⚠️ {failed} unparsable values in '{col}' converted to NaT.")
            except Exception as e:
                log.append(f"⚠️ Failed to parse '{col}' due to error: {str(e)}")

    if not log and verbose:
        log.append("ℹ️ No columns parsed as dates")

    return df, log_lines


def handle_missing_values(df, numeric_strategy, non_numeric_strategy, logger=None, verbose=verbose):
    if logger is None:
        logger = lambda *args, **kwargs: None  # no-op if not passed

    log_lines = []

    for col in df.columns:
        is_numeric = pd.api.types.is_numeric_dtype(df[col])

        # Check for missing values (NaN or blank strings for non-numeric)
        has_nulls = df[col].isnull().any()
        has_empty = (df[col] == "").any() if not is_numeric else False
        has_nans = df[col].isnull().sum()
        logger(f"##DEBUG: has_nans = {has_nans} in {df[col]}.")
        if is_numeric:
            if has_nulls:
                num_missing = df[col].isnull().sum()
                if numeric_strategy == "unknown":
                    df[col] = df[col].fillna(-1)
                    log_lines.append(f"🪄 Filled {num_missing} missing values in numeric column '{col}' with -1.")
                    logger(f"##DEBUG: Filled Filled {num_missing} missing values in numeric column '{col}' with -1.")
                elif numeric_strategy == "average":
                    mean = df[col].mean()
                    df[col] = df[col].fillna(df[col].mean())
                    log_lines.append(f"📊 Filled {num_missing} missing values in numeric column '{col}' with {mean}.")
                    logger(f"##DEBUG: Filled {num_missing} missing values in numeric column '{col}' with {mean}.")
                else:
                    if verbose:
                        log_lines.append(f"✅ Numeric column '{col}' left unchanged (Ignored).")
                    logger(f"##DEBUG:  Numeric column '{col}' left unchanged (Ignored).")
            elif verbose:
                log_lines.append(f"✅ Numeric column '{col}' had no missing values.")
        else:
            if non_numeric_strategy == "unknown":
                blanks = df[col].apply(lambda x: isinstance(x, str) and x.strip() == "").sum()
                logger(f"##DEBUG: Blank-looking strings in '{col}':", blanks)

                # Only cast if blanks are found
                if blanks > 0:
                    df[col] = df[col].astype(str)
                    df[col] = df[col].replace(r'^\s*$', np.nan, regex=True)
                    logger(f"##DEBUG: blanks are replaced with nan in '{col}':", blanks)

                # Count real NaNs now
                non_num_missing = df[col].isnull().sum()
                logger(f"##DEBUG: non num missing count is {non_num_missing}.")
                if non_num_missing > 0:
                    df[col] = df[col].fillna("Unknown")
                    log_lines.append(f"🪄 Filled {non_num_missing} missing values in non-numeric column '{col}' with 'Unknown'")
                    logger(f"##DEBUG: Filled {non_num_missing} missing values in non-numeric column '{col}' with 'Unknown'")
            elif non_numeric_strategy == "mode":
                mode = df[col].mode() 
                logger(f"##DEBUG: mode = {mode}")
                df[col] = df[col].replace(r'^\s*$', np.nan, regex=True)
                
                if not mode.empty:
                    non_num_missing = df[col].isnull().sum()
                    df[col] = df[col].fillna(mode[0])
                    log_lines.append(f"🪄 Filled {non_num_missing} missing values in non-numeric column '{col}' with '{mode}'.")
                    logger(f"##DEBUG:  Filled {non_num_missing} missing values in non-numeric column '{col}' with '{mode}'.")
                else:
                    log_lines.append(f"📉 No valid mode found for non-numeric column '{col}' — no changes made.")
            else:
                logger(f"##DEBUG: no text missing in {df[col]}.")


    return df, log_lines

def write_log(cleaned_df):
    return cleaned_df.attrs.get("log", ["No cleaning log available."])

#def final_sanity_check(df):
    #possibly add functionality later if customer wants to drop columns where all values are missing