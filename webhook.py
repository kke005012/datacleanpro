from flask import Flask, request
import stripe
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import datetime

app = Flask(__name__)

# Stripe secret
stripe.api_key = "sk_test_51RrkXF5E9ltgP0hOrpvWUA8vuKwEINaRy2Nb10tqroDAhYPTHVi2HNKHy4yq0cdiOmfIq0KoCUW5CHkIyCHoRPci00YaBmNcNO"  # replace with your test secret key
endpoint_secret = "whsec_..."   # from Stripe dashboard after webhook setup

# Google Sheets setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "google_creds.json"  # replace with your service account JSON

SPREADSHEET_ID = "..."  # your existing usage log sheet ID

def log_payment_to_sheet(email, amount, filename):
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    now = datetime.datetime.now().isoformat()
    sheet.append_row([now, email, filename, amount / 100, payment_status])

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return f"⚠️ Webhook error: {e}", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")
        amount = session.get("amount_total")
        metadata = session.get("metadata", {})
        filename = metadata.get("filename", "unknown.csv")

        log_payment_to_sheet(email, amount, filename)
        return "✅ Payment logged", 200

    return "Unhandled event", 200
