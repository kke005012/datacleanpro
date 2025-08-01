import smtplib
from email.mime.text import MIMEText
import streamlit as st

def send_feedback_email(entry):
    import smtplib
    from email.mime.text import MIMEText
    import streamlit as st

    body = f"""📬 New Feedback Received

Category: {entry['category']}
Message:
{entry['message']}

From: {entry['name']} <{entry['email'] or 'Not Provided'}>
Timestamp: {entry['timestamp']}
"""

    msg = MIMEText(body)
    msg['Subject'] = "📬 New Feedback - DataCleanPro"
    msg['From'] = st.secrets["smtp_user"]
    msg['To'] = "admin@datacleanpro.com"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(
                st.secrets["smtp_user"],
                st.secrets["smtp_app_password"]
            )
            server.send_message(msg)
    except Exception:
        pass
