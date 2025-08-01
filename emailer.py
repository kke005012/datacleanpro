# emailer.py

import smtplib
from email.mime.text import MIMEText

def send_feedback_email(entry):
    body = f"""New Feedback Received

Category: {entry['category']}
Message:
{entry['message']}

From: {entry['name']} <{entry['email'] or 'Not Provided'}>
Timestamp: {entry['timestamp']}
"""

    msg = MIMEText(body)
    msg['Subject'] = "📬 New Feedback - DataCleanPro"
    msg['From'] = "datacleanpro2025@gmail.com"
    msg['To'] = "datacleanpro2025@gmail.com"

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("admin@datacleanpro.com", st.secrets["gmail"]["password"])
        server.send_message(msg)
