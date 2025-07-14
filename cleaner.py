import pandas as pd
from datetime import datetime

def strip_whitespace(df, log_lines):
    """Strip leading/trailing whitespace from all string columns and log changes."""
    for col in df.select_dtypes(include='object'):
        before = df[col].copy()
        df[col] = df[col].str.strip()
        changed = (before != df[col]).sum()
        if changed > 0:
            log_lines.append(f"🔠 Stripped whitespace in {changed} cells of column '{col}'")
    return df

def drop_empty_rows(df, log_lines):
    """Drop rows where all values are missing and log the count."""
    before = len(df)
    df = df.dropna(how='all')
    dropped = before - len(df)
    if dropped > 0:
        log_lines.append(f"🧹 Dropped {dropped} fully empty rows")
    return df

def deduplicate(df, log_lines):
    """Remove exact duplicate rows and log the count."""
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    if removed > 0:
        log_lines.append(f"🔁 Removed {removed} duplicate rows")
    return df

def clean_data(df, log_lines=None):
    """
    Run all basic cleaning steps on the DataFrame.
    Optionally logs each transformation to the log_lines list.
    """
    if log_lines is None:
        log_lines = []

    df = df.copy()
    df = strip_whitespace(df, log_lines)
    df = drop_empty_rows(df, log_lines)
    df = deduplicate(df, log_lines)

    return df

def write_log(log_lines, filename=None):
    """
    Write cleaning summary log to a .log file.
    Returns the filename for later download.
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"cleaning_log_{timestamp}.log"

    with open(filename, "w") as f:
        f.write("🧼 DataCleanPro Cleaning Summary Log\n")
        f.write(f"📅 Timestamp: {datetime.now().isoformat()}\n\n")
        for line in log_lines:
            f.write(f"{line}\n")

    return filename
