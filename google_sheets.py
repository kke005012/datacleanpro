import json
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

def append_log_to_sheet(log_entry, spreadsheet_id):
    # ✅ Parse credentials from secrets
    creds_dict = json.loads(st.secrets["gcp_service_account"])

    # ✅ Build credentials object
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    # ✅ Connect and write
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.sheet1  # or by name
    worksheet.append_row(list(log_entry.values()))