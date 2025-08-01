import gspread
from google.oauth2.service_account import Credentials

def append_log_to_sheet(log_entry: dict, spreadsheet_id: str, sheet_name: str = "Logs"):
    # Define scope and authorize using credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    client = gspread.authorize(creds)

    # Open the spreadsheet by ID
    sheet = client.open_by_key(spreadsheet_id)

    # Select or create the desired sheet
    try:
        worksheet = sheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
        worksheet.append_row(list(log_entry.keys()))  # Add headers on first creation

    # Append the log values
    worksheet.append_row(list(log_entry.values()))
