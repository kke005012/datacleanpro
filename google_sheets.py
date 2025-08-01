import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

def append_log_to_sheet(log_entry, spreadsheet_id):
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(spreadsheet_id).sheet1

    # Write the log entry
    sheet.append_row([
        log_entry["timestamp"],
        log_entry["email"],
        log_entry["filename"],
        log_entry["row_count"],
        log_entry["charged"]
    ])