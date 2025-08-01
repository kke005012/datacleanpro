import pandas as pd
import numpy as np
import re
from dateutil import parser
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

# --- cleaner.py ---

verbose = False 

def clean_data(df, numeric_strategy="ignore", non_numeric_strategy="ignore"):  # add logger=None if debug mode is turned on in app.py
    #if logger is None:
        #logger = lambda *args, **kwargs: None  # no-op if not passed

    log_lines = []

    # 1. Strip whitespace
    strip_log = []
    if non_numeric_strategy.lower() in ["ignore", "unknown"]:
        df, strip_log = strip_whitespace(df, strategy=non_numeric_strategy.lower())
    log_lines.extend(strip_log)

    # 2. Drop empty rows
    df, drop_log = drop_empty_rows(df, verbose=verbose)
    log_lines.extend(drop_log)

    # 3. Deduplicate
    df, dedup_log = deduplicate(df, verbose=verbose)
    log_lines.extend(dedup_log)

    # 4. Standardize column names
    df, colname_log = standardize_column_names(df, verbose=verbose)
    log_lines.extend(colname_log)

    # 5. Clean currency columns
    df, currency_log = clean_currency_columns(df, numeric_strategy=numeric_strategy, verbose=verbose)
    log_lines.extend(currency_log)

    # 6. Normalize date columns
    df, date_log = normalize_dates(df, verbose=verbose)
    log_lines.extend(date_log)

    # 7. Handle missing values
    df, missing_log = handle_missing_values(df, numeric_strategy, non_numeric_strategy, verbose=verbose)
    log_lines.extend(missing_log)

    # 8. (Optional) Final sanity check
    # df = final_sanity_check(df)
    # log_lines.append("Performed final sanity checks")

    # Attach log for export or UI display
    df.attrs["log"] = log_lines

    return df

def strip_whitespace(df, strategy="ignore", verbose=True):
    log = []
    for col in df.columns:
        if df[col].dtype == object or df[col].dtype.name == "category":
            # Save original null mask
            original_nulls = df[col].isna()
            
            # Only apply strip to non-nulls
            stripped = df[col].where(original_nulls, df[col].astype(str).str.strip())
            # Re-assign column
            df[col] = stripped

            # Now detect new NaNs introduced *after* strip
            new_nulls = df[col].isna() & ~original_nulls
            num_new_nulls = new_nulls.sum()

            if num_new_nulls > 0:
                if strategy == "unknown":
                    df.loc[new_nulls, col] = "Unknown"
                elif strategy == "ignore":
                    df.loc[new_nulls, col] = ""

            if verbose:
                log.append(
                    f"🧹 Stripped whitespace in '{col}'."
                )

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


def is_likely_currency(val):
    if not isinstance(val, str):
        val = str(val)

    val = val.strip()

    # Must include a currency signal — $, comma, decimal, or parentheses
    if not any(x in val for x in ["$", ",", ".", "(", ")"]):
        return False

    currency_pattern = re.compile(
        r"^\(?-?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\)?$|^\(?-?\$?\d+(?:\.\d{2})?\)?$"
    )

    return bool(currency_pattern.match(val))


def round_currency(val):
    try:
        return str(Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_DOWN))
    except:
        return np.nan


def clean_currency_columns(df, numeric_strategy="ignore", verbose=False):

    log = []

    def round_currency(val):
        try:
            return Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        except:
            return np.nan

    for col in df.columns:
        if df[col].dtype != object:
            continue

        sample = df[col].dropna().astype(str).head(10).tolist()
        if not any(is_likely_currency(v) for v in sample):
            if verbose:
                log.append(f"ℹ️ Skipped '{col}': no currency-like patterns found.")
            continue

        try:
            # Step 1: Clean and round
            def convert(val):
                if pd.isna(val):
                    return np.nan
                val = str(val).strip().replace("$", "").replace(",", "")
                val = re.sub(r"[()]", "", val)
                return round_currency(val)

            df[col] = df[col].apply(convert)

            # Step 2: Handle missing values according to strategy
            missing_total = df[col].isna().sum()
            filled = 0

            if numeric_strategy == "unknown":
                df[col] = df[col].astype(object).fillna("Unknown")
                filled = (df[col] == "Unknown").sum()

            elif numeric_strategy == "ignore":
                df[col] = df[col].astype(object).fillna("")
                filled = (df[col] == "").sum()

            elif numeric_strategy == "average":
                try:
                    mean_val = df[col].dropna().mean()
                    mean_val = round_currency(mean_val)
                    df[col] = df[col].fillna(mean_val)
                    filled = (df[col] == mean_val).sum()
                except:
                    log.append(f"⚠️ Could not calculate average for column '{col}' — left missing values as is.")

            # Step 3: Convert all final values to string
            df[col] = df[col].apply(lambda x: str(x) if not pd.isna(x) else "")

            msg = f"💲 Cleaned '{col}' as currency. Parsed: {len(df) - missing_total}, Filled: {filled}, Strategy: {numeric_strategy}."
            log.append(msg)

            # Mark this column to skip in handle_missing_values()
            df.attrs.setdefault("currency_columns", []).append(col)

        except Exception as e:
            err_msg = f"⚠️ Failed to clean '{col}' as currency: {str(e)}."
            log.append(err_msg)

    return df, log



def is_likely_date(val):
    if not isinstance(val, str):
        val = str(val)
    val = val.strip().lower()
    if any(month in val for month in [
        "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "oct", "nov", "dec"
    ]):
        return True
    if "t" in val and "z" in val:
        return True
    import re
    if re.match(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", val):
        return True
    if re.match(r"\d{4}[./-]\d{1,2}[./-]\d{1,2}", val):
        return True
    if re.match(r"\d{8}$", val):
        return True
    if re.match(r"\d{1,2}-[a-z]{3}-\d{2,4}", val):
        return True
    return False


def normalize_dates(df, verbose=False):
    log = []

    # Supported date formats — order matters (more specific first)
    date_formats = [
        "%m/%d/%Y %H:%M",        # 7/19/2025 14:30
        "%Y-%m-%dT%H:%MZ",       # 2025-07-19T14:30Z
        "%Y%m%d",                # 19680719
        "%d-%b-%y",              # 19-Jul-25
        "%A, %B %d, %Y",         # Saturday, July 19, 2026
        "%d/%m/%Y",              # 19/09/2000
        "%Y.%m.%d",              # 2025.07.18
        "%m/%d/%Y",              # fallback — 7/19/2025
    ]

    def try_formats(val):
        if pd.isna(val) or str(val).strip().upper() in ["NAN", "NULL", "", "UNKNOWN"]:
            return "Unknown"
        val = str(val).strip()
        for fmt in date_formats:
            try:
                dt = datetime.strptime(val, fmt)
                return dt.strftime("%m-%d-%Y")
            except Exception:
                continue
        return "Unknown"

    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().astype(str).head(10).tolist()
            match_count = sum(1 for val in sample if try_formats(val) != "Unknown")

            if match_count >= 3:
                df[col] = df[col].apply(try_formats)
                unknowns = (df[col] == "Unknown").sum()
                parsed = len(df) - unknowns
                log.append(f"📅 Normalized '{col}' as date. Parsed: {parsed}, Unknown: {unknowns}.")
            elif verbose:
                log.append(f"ℹ️ Skipped '{col}': not enough recognizable dates.")

    return df, log


def is_junk_text(val):
    if pd.isna(val):
        return True

    val_str = str(val).strip()

    # Empty string is junk
    if val_str == "":
        return True

    # If it's only special symbols, that's junk
    if re.fullmatch(r"[\W_]+", val_str):  # matches strings like "!@#", "____"
        return True

    # If it's a single character and not alphanumeric, it's probably junk
    if len(val_str) == 1 and not val_str.isalnum():
        return True

    # Safe default: not junk
    return False


def is_column_actually_numeric(series):
    try:
        pd.to_numeric(series.dropna().astype(str))
        return True
    except Exception:
        return False


def handle_missing_values(df, numeric_strategy="ignore", non_numeric_strategy="ignore", verbose=True):
    log = []

    for col in df.columns:
        # Skip likely date columns
        if any(is_likely_date(val) for val in df[col].dropna().astype(str).head(10)):
            if verbose:
                log.append(f"📆 Skipping missing value handling for likely date column '{col}'.")
            continue

        # Get list of currency columns to be skipped by handle_missing_values
        currency_cols = df.attrs.get("currency_columns", [])
        for col in df.columns:
            if col in currency_cols:
                if verbose:
                    log.append(f"💵 Skipped '{col}' in missing value handler — already processed as currency.")
            continue

        # --- Step 1: Run heuristic ---
        sample = df[col].dropna().astype(str).head(50)
        numeric_like = pd.to_numeric(sample, errors="coerce").notna().sum()
        is_numeric_like = numeric_like / len(sample) > 0.7 if len(sample) > 0 else False

        # --- Step 2: Handle numeric-like columns ---
        if is_numeric_like:
            original_col = df[col].copy()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            missing_total = df[col].isna().sum()
            junk_count = (original_col.notna() & df[col].isna()).sum()

        if pd.api.types.is_numeric_dtype(df[col]):
           original_non_na = df[col].notna().sum()
           missing_total = df[col].isna().sum()
           original_col = df[col].copy()
           df[col] = pd.to_numeric(df[col], errors="coerce")
           coerced_na = df[col].isna().sum() - (df.shape[0] - original_non_na)
           junk_count = (original_col.notna() & df[col].isna()).sum()

           if numeric_strategy == "unknown":
               if df[col].isna().sum() > 0:
                   df[col] = df[col].astype(object).fillna("Unknown")
                   log.append(
                       f"🔧 Replaced {missing_total} missing or invalid values in numeric column '{col}' with 'Unknown'."
                   )

           elif numeric_strategy == "ignore":
               if df[col].isna().sum() > 0:
                   df[col] = df[col].astype(object).fillna("")
                   log.append(
                   f"ℹ️ Left {missing_total} missing or invalid values in numeric column '{col}' as blank (Ignore strategy)."
                   )

        else:
            if non_numeric_strategy == "unknown":
                # Replace junk values and empty/NaN with 'Unknown'
                junk_mask = df[col].apply(is_junk_text)
                junk_count = junk_mask.sum()
                if junk_count > 0:
                    df[col] = df[col].mask(junk_mask, "Unknown")
                    log.append(f"🛠️ Replaced {junk_count} missing or invalid values in text column '{col}' with 'Unknown'.")

            elif non_numeric_strategy == "mode":
                try:
                    mode_val = df[col].mode(dropna=True).iloc[0]
                    junk_mask = df[col].apply(is_junk_text)
                    junk_count = junk_mask.sum()
                    if junk_count > 0:
                        df[col] = df[col].mask(junk_mask, mode_val)
                        log.append(f"🛠️ Replaced {junk_count} missing or invalid values in text column '{col}' with mode value: '{mode_val}'.")

                except Exception:
                    log.append(f"⚠️ Unable to compute mode for column '{col}' — no replacement applied.")
            else:
                # Ignore strategy: do nothing
                if verbose:
                    log.append(f"🚫 Ignored missing value handling for text column '{col}'")


        # For numeric_strategy == "average"
        if pd.api.types.is_numeric_dtype(df[col]) and numeric_strategy == "average":
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                mean_val = df[col].mean()
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    df[col] = df[col].fillna(mean_val)
                    log.append(f"🛠️ Replaced {missing_count} missing values in numeric column '{col}' with mean value: {mean_val:.2f}.")
                    
            except Exception:
                log.append(f"⚠️ Unable to compute mean for numeric column '{col}' — no replacement applied.")

    return df, log


def write_log(cleaned_df):
    return cleaned_df.attrs.get("log", ["No cleaning log available."])

#def final_sanity_check(df):
    #possibly add functionality later if customer wants to drop columns where all values are missing