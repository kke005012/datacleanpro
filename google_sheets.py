import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import traceback

#Log usage to google sheet
def append_log_to_sheet(log_entry: dict):
    try:
        credentials_dict = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)

        spreadsheet_id = st.secrets["google_sheet_id"]
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(spreadsheet_id).sheet1

        row = [
            log_entry["timestamp"],
            log_entry["email"],
            log_entry["filename"],
            log_entry["row_count"],
            log_entry["charged"],
            log_entry["payment_status"]
        ]

        sheet.append_row(row)
    except Exception as e:
        import traceback
        st.warning(f"⚠️ Failed to log usage: {e}")
        st.text(traceback.format_exc())  # Print full stack trace in Streamlit


# Write to feedback tab of google sheet
def append_feedback_to_sheet(entry):
    import gspread
    from google.oauth2.service_account import Credentials
    import streamlit as st

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)

    spreadsheet_id = st.secrets["google_sheet_id"]
    sheet = client.open_by_key(spreadsheet_id)

    try:
        tab = sheet.worksheet("Feedback")
    except gspread.exceptions.WorksheetNotFound:
        tab = sheet.add_worksheet(title="Feedback", rows="1000", cols="5")
        tab.append_row(["timestamp", "category", "message", "name", "email"])

    # Fail silently if append fails
    try:
        tab.append_row([
            entry["timestamp"],
            entry["category"],
            entry["message"],
            entry["name"],
            entry["email"]
        ])
    except Exception:
        pass
