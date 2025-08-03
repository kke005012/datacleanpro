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
                row.get("email") == email
                and row.get("filename") == filename
                and row.get("Paid via webhook") == "Paid via webhook"
            ):
                return True
        return False

    except Exception as e:
        print("⚠️ Error checking payment log:", e)
        return False
