import streamlit as st
import gspread
from google.oauth2.service_account import Credentials



def append_log_to_sheet(log_entry: dict, spreadsheet_id: str):
    try:
        credentials_dict = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)

        client = gspread.authorize(credentials)
        sheet = client.open_by_key(spreadsheet_id).sheet1

        row = [
            log_entry["timestamp"],
            log_entry["email"],
            log_entry["filename"],
            log_entry["row_count"],
            log_entry["charged"]
        ]

        sheet.append_row(row)
    except Exception as e:
        import traceback
        st.warning(f"⚠️ Failed to log usage: {e}")
        st.text(traceback.format_exc())  # Print full stack trace in Streamlit
