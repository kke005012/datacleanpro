# mailer.py

import smtplib
from email.message import EmailMessage
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import streamlit as st

def send_receipt(
    to_email,
    filename,
    amount,
    cleaning_strategies,
    log_lines,
    smtp_user,
    smtp_app_password
):
    msg = MIMEMultipart()
    msg["Subject"] = f"DataClean Pro Receipt — {filename}"
    msg["From"] = f"DataCleanPro <{smtp_user}>"
    msg["To"] = to_email
    msg["Bcc"] = "datacleanpro2025@gmail.com"

    # Construct HTML receipt
    strategies_html = "".join(f"<li>{strategy}</li>" for strategy in cleaning_strategies)
    html = f"""
    <html>
        <body>
            <h2>🧾 Receipt — DataClean Pro</h2>
            <p><strong>Filename:</strong> {filename}</p>
            <p><strong>Amount Charged:</strong> ${amount:.2f}</p>
            <p><strong>Date/Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Cleaning Strategies:</strong></p>
            <ul>{strategies_html}</ul>
            <p>Thank you for using DataClean Pro!</p>
        </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    # Attach log
    if log_lines:
        log_text = "\n".join(log_lines)
        log_part = MIMEApplication(log_text, _subtype="txt")
        log_part.add_header("Content-Disposition", "attachment", filename="cleaning_log.txt")
        msg.attach(log_part)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_app_password)
            server.send_message(msg)
        return True, "📬 Receipt sent successfully."
    except Exception as e:
        return False, f"Failed to send email: {e}"



####Test email set-up
def send_test_email():
    smtp_user = st.secrets["smtp_user"]
    smtp_app_password = st.secrets["smtp_app_password"]

    msg = MIMEText("This is a test email from DataCleanPro — success! ✅")
    msg["Subject"] = "Test Email from DataCleanPro"
    msg["From"] = "DataCleanPro <admin@datacleanpro.com>"
    msg["To"] = "kristi.esta@gmail.com"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_app_password)
            smtp.send_message(msg)
        st.success("✅ Test email sent successfully!")
    except Exception as e:
        st.error(f"❌ Failed to send email: {str(e)}")

