# mailer.py

import smtplib
from email.message import EmailMessage
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import streamlit as st

def send_receipt(to_email, amount, filename, cleaning_strategies, log_lines, smtp_user, smtp_app_password):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Your DataCleanPro Cleaning Receipt"
        msg["From"] = "admin@datacleanpro.com"
        msg["To"] = to_email

        date_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        summary = f"""
Hi there,

Your file **{filename}** was successfully cleaned on {date_str}.

Here’s what we did:
- Numeric Strategy: {cleaning_strategies.get('numeric', 'N/A')}
- Non-Numeric Strategy: {cleaning_strategies.get('non_numeric', 'N/A')}
- Currency Strategy: {cleaning_strategies.get('currency', 'N/A')}

✅ Total cleaning steps: {len(log_lines)}
💲 Amount charged: ${amount:.2f}

The full cleaning log is attached for your records.

Thanks for using DataClean Pro!  
The DataCleanPro Team
"""

        msg.set_content(summary)

        # Attach the cleaning log
        log_text = "\n".join(log_lines)
        msg.add_attachment(log_text, subtype="plain", filename="cleaning_log.txt")

        # Send via Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_app_password)
            smtp.send_message(msg)

        return True, "✅ Receipt sent successfully."

    except Exception as e:
        return False, f"⚠️ Receipt failed to send: {e}"


def send_receipt(to_email, filename, amount, cleaning_strategies, log_lines, smtp_user, smtp_app_password):
    # Format the timestamp
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Email body (HTML)
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2 style="color: #2c3e50;">DataCleanPro Receipt</h2>
        <p>Thank you for using <strong>DataCleanPro</strong>!</p>
        <p><strong>File:</strong> {filename}<br>
        <strong>Amount Charged:</strong> ${amount:.2f}<br>
        <strong>Date:</strong> {timestamp}</p>
        <p><strong>Cleaning Strategies Applied:</strong></p>
        <ul>
    """

    for strategy in cleaning_strategies:
        html += f"<li>{strategy}</li>"
    html += """
        </ul>
        <p>A detailed log of your cleaning session is attached for your records.</p>
        <p style="color: #888;">If you have questions, reply to this email or contact support@datacleanpro.com.</p>
    </body>
    </html>
    """

    # Construct message
    msg = MIMEMultipart()
    msg["Subject"] = "Your DataCleanPro Cleaning Receipt"
    msg["From"] = f"DataCleanPro <{smtp_user}>"
    msg["To"] = to_email
    msg["Bcc"] = "admin@datacleanpro.com"

    msg.attach(MIMEText(html, "html"))

    # Attach log
    log_text = "\n".join(log_lines)
    attachment = MIMEApplication(log_text.encode("utf-8"), Name="cleaning_log.txt")
    attachment["Content-Disposition"] = 'attachment; filename="cleaning_log.txt"'
    msg.attach(attachment)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_app_password)
            server.send_message(msg)
        return True, "✅ Receipt email sent successfully!"
    except Exception as e:
        return False, f"❌ Failed to send receipt email: {e}"


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

