import smtplib
from email.mime.text import MIMEText
import streamlit as st

def send_feedback_email(entry):
    smtp_user = st.secrets["smtp_user"]
    smtp_pass = st.secrets["smtp_app_password"]

    body = f"""📬 New Feedback Received

Category: {entry['category']}
Message:
{entry['message']}

From: {entry['name']} <{entry['email'] or 'Not Provided'}>
Timestamp: {entry['timestamp']}
"""

    msg = MIMEText(body)
    msg['Subject'] = "📬 New Feedback - DataCleanPro"
    msg['From'] = smtp_user  # must match login
    msg['To'] = "datacleanpro2025@gmail.com"

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
