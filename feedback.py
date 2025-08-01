# feedback.py

import streamlit as st
from datetime import datetime
from google_sheets import append_feedback_to_sheet
from emailer import send_feedback_email
import traceback

def show_sidebar_feedback():
    with st.sidebar:
        st.markdown("---")
        st.markdown("#### 💬 Feedback")

        with st.form("sidebar_feedback_form"):
            category = st.selectbox(
                "Type",
                ["Improvement Suggestion", "Bug Report", "Feature Request", "Other"],
                key="feedback_category"
            )
            message = st.text_area("Your Message", placeholder="Tell us more...", height=120, key="feedback_message")
            name = st.text_input("Name (optional)", key="feedback_name")
            email = st.text_input("Email (optional)", key="feedback_email")

            submitted = st.form_submit_button("Submit")

            if submitted:
                if not message.strip():
                    st.warning("Please enter a message.")
                    return

                feedback_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "category": category,
                    "message": message.strip(),
                    "name": name.strip(),
                    "email": email.strip()
                }

                try:
                    append_feedback_to_sheet(feedback_entry)
                except Exception as e:
                    st.warning("⚠️ Feedback submitted, but logging failed.")
                    st.text(f"❌ Error: {e}")  # Show actual error in app
                    traceback.print_exc()     # Log full error to terminal

                try:
                    send_feedback_email(feedback_entry)
                except Exception as e:
                    print("⚠️ Feedback email error:", e)

                st.success("✅ Thank you for your feedback!")
