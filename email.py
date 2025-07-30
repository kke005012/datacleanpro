# mailer.py

import smtplib
from email.message import EmailMessage
from datetime import datetime
from email.mime.text import MIMEText
import streamlit as st

def send_receipt(to_email, amount, filename, strategy_dict, log_lines, smtp_user, smtp_app_password):
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
- Numeric Strategy: {strategy_dict.get('numeric', 'N/A')}
- Non-Numeric Strategy: {strategy_dict.get('non_numeric', 'N/A')}
- Currency Strategy: {strategy_dict.get('currency', 'N/A')}

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


####Test email set-up
def send_test_email():
    smtp_user = st.secrets["smtp_user"]
    smtp_app_password = st.secrets["smtp_app_password"]

    msg = MIMEText("This is a test email from DataCleanPro — success! ✅")
    msg["Subject"] = "Test Email from DataCleanPro"
    msg["From"] = "DataCleanPro <admin@datacleanpro.com>"
    msg["To"] = "kristi.esta@gmail.com"  # replace with test inbox

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_app_password)
            smtp.send_message(msg)
        st.success("✅ Test email sent successfully!")
    except Exception as e:
        st.error(f"❌ Failed to send email: {str(e)}")

