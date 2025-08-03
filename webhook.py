from flask import Flask, request
import stripe
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import datetime

app = Flask(__name__)

# Stripe secret
# Secure Stripe config
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

# Google Sheets setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# Google Sheets config
CREDS_FILE = os.environ.get("GOOGLE_CREDS_FILE", "google_creds.json")
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]

def log_payment_to_sheet(email, amount, filename):
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    now = datetime.datetime.now().isoformat()
    payment_status = "Paid via webhook"
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
