import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os


def was_payment_logged(email, filename):
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            os.environ.get("GOOGLE_CREDS_FILE", "google_creds.json"),
            scopes=[
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(os.environ["SPREADSHEET_ID"]).sheet1
        records = sheet.get_all_records()

        for row in records:
            if (
                row.get("email", "").strip().lower() == email.strip().lower()
                and row.get("filename", "").strip().lower() == filename.strip().lower()
                and row.get("payment_status", "").strip().lower() == "paid via webhook"  
            ):
                return True
        return False

    except Exception as e:
        print("⚠️ Error checking payment log:", e)
        return False
