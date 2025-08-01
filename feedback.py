# feedback.py
import streamlit as st
from datetime import datetime
from google_sheets import append_feedback_to_sheet
from emailer import send_feedback_email

def show_sidebar_feedback():
    with st.sidebar:
        st.markdown("---")
        st.markdown("#### 💬 Feedback Form")

        with st.form("sidebar_feedback_form"):
            category = st.selectbox(
                "Type",
                ["Improvement Suggestion", "Bug Report", "Feature Request", "Other"],
                key="feedback_category"
            )
            message = st.text_area("Your Message", placeholder="Tell us more...", height=120, key="feedback_message")
            name = st.text_input("Name (optional)", key="feedback_name")
            email = st.text_input("Email *", key="feedback_email")

            submitted = st.form_submit_button("Submit")

            if submitted:
                if not message.strip() or not email.strip() or "@" not in email or "." not in email:
                    return  # silently ignore bad inputs

                feedback_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "category": category,
                    "message": message.strip(),
                    "name": name.strip(),
                    "email": email.strip()
                }

                # Try logging and emailing, but fail silently
                try:
                    append_feedback_to_sheet(feedback_entry)
                except Exception:
                    pass

                try:
                    send_feedback_email(feedback_entry)
                except Exception:
                    pass

                st.success("✅ Thank you for your feedback!")
