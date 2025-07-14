import pandas as pd
import numpy as np
from datetime import datetime



def strip_whitespace(df):
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip()
    return df


def drop_empty_rows(df):
    return df.dropna(how='all')


def deduplicate(df):
    return df.drop_duplicates()


def standardize_column_names(df):
    df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_").str.replace(r'[^a-zA-Z0-9_]', '', regex=True)
    return df


def clean_currency_columns(df, log_lines):
    for col in df.columns:
        if df[col].dtype == object and df[col].str.contains(r'\$|\,').any():
            try:
                df[col] = df[col].replace({r'\$': '', ',': ''}, regex=True).astype(float)
                log_lines.append(f"Converted currency strings in column '{col}' to float.")
            except:
                log_lines.append(f"Failed to convert column '{col}' to float.")
    return df


def normalize_dates(df, log_lines):
    for col in df.columns:
        if df[col].dtype == object:
            try:
                parsed_dates = pd.to_datetime(df[col], errors='coerce')
                if parsed_dates.notnull().sum() > 0:
                    df[col] = parsed_dates
                    log_lines.append(f"Normalized date values in column '{col}'.")
            except:
                continue
    return df


def handle_missing_values(df, fill_with_mode=False, log_lines=None):
    for col in df.columns:
        if df[col].dtype == object:
            if fill_with_mode:
                mode_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
                df[col].fillna(mode_val, inplace=True)
                if log_lines is not None:
                    log_lines.append(f"Filled missing values in '{col}' with mode: {mode_val}")
            else:
                df[col].fillna('Unknown', inplace=True)
                if log_lines is not None:
                    log_lines.append(f"Filled missing values in '{col}' with 'Unknown'")
        else:
            df[col].fillna(df[col].mean(), inplace=True)
            if log_lines is not None:
                log_lines.append(f"Filled missing values in '{col}' with column mean")
    return df


def final_sanity_check(df, log_lines):
    initial_cols = df.columns.tolist()
    df = df.loc[:, ~df.columns.duplicated()]
    if len(df.columns) != len(initial_cols):
        log_lines.append("Removed duplicate column names during final sanity check.")
    return df


def clean_data(df, log_lines=None):
    if log_lines is None:
        log_lines = []
    df = strip_whitespace(df)
    df = drop_empty_rows(df)
    df = deduplicate(df)
    log_lines.append("Stripped whitespace, dropped empty rows, and removed duplicates.")
    return df


def write_log(log_lines, log_filename="cleaning_log.txt"):
    with open(log_filename, "w") as f:
        f.write("Cleaning Summary:\n")
        for line in log_lines:
            f.write(f"- {line}\n")
    return log_filename
