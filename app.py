# === app.py ===
import streamlit as st
import pandas as pd
import gspread
import matplotlib.pyplot as plt
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
import hashlib
from mailer import send_receipt
import smtplib
from email.mime.text import MIMEText
import os
import csv
from google_sheets import append_log_to_sheet
from feedback import show_sidebar_feedback
from checkout import create_checkout_session
from payment import was_payment_logged
import stripe

from cleaner import (
    clean_data,
    strip_whitespace,
    drop_empty_rows,
    deduplicate,
    write_log,
    standardize_column_names,
    clean_currency_columns,
    normalize_dates,
    handle_missing_values
)
from pricing import calculate_price

def logger(*args):
    st.write(*args)

st.markdown(
    """
    <div style='background-color: #d4edda; padding: 5px; text-align: center; margin-bottom: 40px;'>
        <p style='font-size: 15px; color: #155724; margin: 0;'>🧼 <strong>DataClean Pro</strong> is a cloud-based data cleaning app for real-world CSV files.</p>
    </div>
    """,
    unsafe_allow_html=True
)
st.set_page_config(page_title="DataClean Pro | Clean Real-World CSVs Fast", page_icon="🧼", layout="wide")

# Navigation
page = st.sidebar.selectbox("📂 Choose a page", ["Welcome", "Clean My Data"])

if page == "Welcome":
    st.markdown("""
        <h2 style='text-align: center;'>Welcome to DataClean Pro 🧼</h2>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <span style='color:#2B78E4; font-size:1.2em; text-align: center;'>
        &#128338; Save hours. Clean your data in less than a minute — without the dirty price tag. 
        </span>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)  # Adds vertical space

    st.markdown("""
        Whether you're dealing with missing values, inconsistent dates, or currency formatting, we've got you covered.
        Clean your dataset, download your results, and get back to real work — fast.  Pay only for what you clean — no subscriptions, no upsells, no tricks.
    """)

    st.markdown("""
        #### ✅ What We Offer  
        - Upload your messy CSV  
        - Strip whitespace, fix formats, remove duplicates  
        - Replace missing numeric/non-numeric values or leave as-is...your choice! 
    """, unsafe_allow_html=True)

    st.markdown("""
<h4><span>&#x1F4B8;</span> Pricing</h4>
<p><strong>100 rows or less: Free</strong></p>
<p><strong>After that:</strong></p>
<ul style="list-style-type: none; padding-left: 1em;">
  <li><strong>$0.02 per row up to 500 rows</strong></li>
  <li><strong>$0.015 per row up to 1500 rows</strong></li>
  <li><strong>$0.01 per row up to 10,000 rows</strong></li>
  <li><strong>$0.008 per row up to 25,000 rows</strong></li>
  <li><strong>$0.007 per row up to 100,000 rows</strong></li>
  <li><strong>Please contact us for custom pricing beyond 100,000 rows.</strong></li>
</ul>
""", unsafe_allow_html=True)

    st.markdown("""
#### 👈 Use the sidebar to switch to **Clean My Data**
#### 📨 Need Help?  
Email us anytime: [admin@datacleanpro.com](mailto:datacleanpro2025@gmail.com)
""", unsafe_allow_html=True)

elif page == "Clean My Data":
    # Style the buttons
    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #4CAF50; /* soft green */
            color: white;
            padding: 0.6em 1.5em;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #45a049;
            box-shadow: 0 6px 10px rgba(0,0,0,0.15);
        }
        </style>
    """, unsafe_allow_html=True)
 
    st.title("🧹 Clean My Data")

    # Debug logger toggle
    debug_mode = st.checkbox("🛠️ Enable Debug Mode")
    if debug_mode:
        st.info("🔍 Debug Mode is ON — showing internal logs.")
    
    # === Add Header question in sidebar ===
    has_header = st.sidebar.checkbox("Uncheck if columns do not have titles.", value=True)
    # === End Header question in sidebar ===
    
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    # === Capture original filename to use with cleaned on the download ===
    if uploaded_file is not None:
        original_filename = uploaded_file.name
        base_filename = original_filename.rsplit(".", 1)[0]
        download_filename = f"{base_filename}_clean.csv" if uploaded_file else "cleaned_data.csv"
    # === End original filename ===
         
    # === Sidebar Cleaning Options ===
    if "raw_df" in st.session_state and st.session_state.raw_df is not None:
        with st.sidebar:
            st.sidebar.markdown("### 🧹 Cleaning Options")

            st.sidebar.markdown("**Handle Missing Values**")
            numeric_strategy = st.sidebar.radio(
                "Numeric Columns",
                options=["Ignore", "Unknown", "Average"],
                index=0,
                key="missing numeric",
                help="""
                    - **Ignore**: Leaves missing numeric values blank.
                    - **Unknown**: Replaces missing numeric values with -1.
                    - **Average**: Replaces missing values with the column's average.
                """
            )
            
            non_numeric_strategy = st.sidebar.radio(
                "Text Columns",
                options=["Ignore", "Unknown", "Mode"],
                index=0,
                key="missing non-numeric",
                help="""
                    - **Ignore**: Leaves missing text values blank.
                    - **Unknown**: Replaces them with 'Unknown'.
                    - **Mode**: Fills missing values with the most frequent (mode) value in that column.
                """
            )

    # === End of Sidebar Section ===
 
   
    # === Safe session state initialization ===
    
    # Initialize session variables
    if "raw_df" not in st.session_state:
        st.session_state.raw_df = pd.DataFrame()
    if "cleaned_df" not in st.session_state:
        st.session_state.cleaned_df = pd.DataFrame()
    if "file_hash" not in st.session_state:
        st.session_state.file_hash = ""
    if "upload_attempted" not in st.session_state:
        st.session_state.upload_attempted = False

    def get_file_hash(file):
        return hashlib.md5(file.getvalue()).hexdigest()

    # === Load file into session state ===
    if uploaded_file is not None:
        st.session_state.upload_attempted = True
        file_hash = get_file_hash(uploaded_file)

        if st.session_state.file_hash != file_hash:
            # === Handle header/no header ===
            if has_header:
                df = pd.read_csv(uploaded_file, keep_default_na=False, na_values=[""], low_memory=False)
            else:
                df = pd.read_csv(uploaded_file, header=None, keep_default_na=False, na_values=[""], low_memory=False)
                df.columns = [f"column_{i}" for i in range(df.shape[1])]
            # === End Header/No Header ===

            # === Check the number of rows in the DataFrame ===
            if len(df) > 100000:
                st.error(
                    "❌ This app supports a maximum of 100,000 rows. Please upload a smaller file or "
                    "[contact us][admin@datacleanpro.com](mailto:datacleanpro2025@gmail.com) for a custom order/pricing.",
                    icon="🚫"
                )
                st.stop()
            min_rows_required = 1
            if df.empty or len(df) < min_rows_required:
               st.error("❌ This app supports a minimum of 1 row of data. Please upload a valid file.")
               st.stop()
            # ==== End Row Count Check ===                    
 
            st.session_state.raw_df = df.copy()
            st.session_state.cleaned_df = None
            st.session_state.file_hash = file_hash
            st.success("File uploaded!")
        else:
            st.info("Same file detected — using cached version.")
        
        # === Show raw data preview if available ===
        if not st.session_state.raw_df.empty:
            st.write(f"### 📊 Preview of Uploaded Data")
            st.dataframe(st.session_state.raw_df.head())

            # === Cleaning Options ===
            #st.markdown("""
            #<div style='margin-top: 2em; text-align: center;'>
                #<h4> 🛠️ Handle Missing Values</h4>
            #</div>
            #""", unsafe_allow_html=True)

            #st.markdown("""
            #<div style='display: flex; justify-content: center; flex-direction: column; align-items: center;'>
            #""", unsafe_allow_html=True)

            #numeric_strategy = st.radio(
                #"Missing Numeric Values:",
                #["Ignore", "Replace with Unknown", "Use Average"],
                #index=0
            #)

            #non_numeric_strategy = st.radio(
                #"Missing Non-Numeric Values:",
                 #["Ignore", "Replace with Unknown", "Use Mode"],
                 #index=0
            #)

            #st.markdown("</div>", unsafe_allow_html=True)

            # === Clean button only appears if data is ready ===

            if st.button("Clean My Data"):
                cleaned_df = clean_data(
                    st.session_state.raw_df.copy(),
                    numeric_strategy=numeric_strategy.lower(),
                    non_numeric_strategy=non_numeric_strategy.lower(),     #add comma if debug mode is reinstated
                    logger = st.write if debug_mode else None
                )

                st.session_state.cleaned_df = cleaned_df
                st.session_state["cleaning_log"] = cleaned_df.attrs["log"]

        elif st.session_state.upload_attempted:
            st.warning(" ⚠️ No raw data available to clean. Please upload a file.")

        # === Show cleaned data ===
        cleaned_df = st.session_state.get("cleaned_df", None)
        
        if cleaned_df is not None and not cleaned_df.empty:
            st.write("### ✅ Cleaned Data Preview")
            st.dataframe(cleaned_df.head())
            rows, cols = cleaned_df.shape

            row_count = len(cleaned_df)
            cost, rows = calculate_price(row_count)
            st.session_state["row_count"] = row_count
            st.session_state["cost"] = cost
            st.session_state["total_rows"] = rows
            
            if "cost" in st.session_state and "total_rows" in st.session_state:
                st.markdown(f"**Standard Cost: ${st.session_state['cost']:.2f}**. Total Rows = {st.session_state['total_rows']}.")

            if cost == 0:
                st.info("✅ This file qualifies for free cleaning.")
                st.session_state["payment_complete"] = True

            if st.checkbox("Show cleaning log"):
                st.write("### 📋 Cleaning Log")
                log_lines = write_log(cleaned_df)
                if log_lines:
                    for line in log_lines:
                        st.markdown(f"- {line}")
                else:
                    st.info("No cleaning actions were logged.")


            email = st.text_input("📧 Enter your email to receive a receipt *.")
            # Basic format check
            if not email:
                st.warning("⚠️ Please enter your email address to continue.")
                st.stop()
            elif "@" not in email or "." not in email:
                st.warning("⚠️ That doesn’t look like a valid email address.")
                st.stop()
            else:
                st.session_state["user_email"] = email

            filename=uploaded_file.name
            
            ## --- Payment stuff starts            
            if cost > 0:
                if st.button("💳 Pay Now"):
                    checkout_url = create_checkout_session(int(cost * 100), email, filename)
                    if checkout_url:
                        st.markdown(f"[🔗 Click here to complete payment]({checkout_url})", unsafe_allow_html=True)
            else:
                st.success("✅ No payment required — you may download your file.")
            ## --- Payment stuff ends

            ## Check for payment success
            stripe.api_key = st.secrets["stripe"]["secret_key"]

            query_params = st.query_params
            session_id = query_params.get("session_id", [None])[0]

            if query_params.get("status") == ["success"] and session_id:
                try:
                    session = stripe.checkout.Session.retrieve(session_id)
                    st.session_state["user_email"] = session["customer_details"]["email"]
                    st.session_state["payment_complete"] = True
                    st.session_state["paid_filename"] = session["metadata"].get("filename", "unknown.csv")
                    st.success(f"✅ Payment complete for {st.session_state['paid_filename']}")
                except Exception as e:
                    st.warning(f"⚠️ Payment verified, but failed to retrieve session info: {e}")

            # Check for verified payment in the sheet
            if (was_payment_logged(st.session_state["user_email"], filename) or cost == 0) and st.session_state.get("user_email"):
                success, message = send_receipt(
                    to_email=st.session_state["user_email"],
                    filename = filename,
                    amount=cost,
                    cleaning_strategies=[
                        f"Numeric Strategy: {numeric_strategy}",
                        f"Non-Numeric Strategy: {non_numeric_strategy}",
                        "Currency Normalization",
                        "Date Standardization",
                        "Whitespace & Deduplication"
                    ],
                    log_lines=cleaned_df.attrs.get("log", []),
                    smtp_user=st.secrets["smtp_user"],
                    smtp_app_password=st.secrets["smtp_app_password"]
                )
    
                if success:
                    st.success("📧 Your receipt was emailed.")
                else:
                    st.warning(f"⚠️ {message or 'Receipt failed to send.'}")
    
                st.download_button(
                    "📥 Download Cleaned CSV",
                    data=cleaned_df.to_csv(index=False),
                    file_name=download_filename,
                    mime="text/csv"
                )
            else:
                st.info("🔄 Waiting for payment confirmation... Please refresh this page in a few moments.")
            ## --- End of payment / receipt logic

                # ... after sending receipt ...
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "email": st.session_state.get("user_email", "unknown"),
                    "filename": uploaded_file.name,
                    "row_count": len(cleaned_df),
                    "charged": cost,
                }

                try:
                    append_log_to_sheet(log_entry)
                except Exception as e:
                    st.warning(f"⚠️ Failed to log usage: {e}")


    # Show feedback form in the sidebar
    show_sidebar_feedback()

def render_footer():
    st.markdown(
        """
        <style>
        .footer {
            position: fixed;
            bottom: 0;
            right: 0;
            padding: 10px;
            background-color: rgba(255,255,255,0.0);
            z-index: 9999;
        }
        .footer a {
            margin-left: 10px;
            text-decoration: none;
        }
        </style>
            """,
        unsafe_allow_html=True
    )
    
    # Social Media bs
st.markdown("""
<div class="footer" style="text-align: right; margin-top: 50px;">
  <a href="https://www.facebook.com/search/top/?q=dataclean" target="_blank">📘 Facebook</a> |
  <a href="https://www.instagram.com/data.cleanpro" target="_blank">📸 Instagram</a> |
  <a href="https://www.linkedin.com/company/dataclean-pro" target="_blank">💼 LinkedIn</a>
</div>
""", unsafe_allow_html=True)



## Test email function
def send_test_email():
    smtp_user = st.secrets["smtp_user"]
    smtp_app_password = st.secrets["smtp_app_password"]

    msg = MIMEText("This is a test email from DataCleanPro — success! ✅")
    msg["Subject"] = "Test Email from DataCleanPro"
    msg["From"] = f"DataCleanPro <{smtp_user}>"
    msg["To"] = "kristi.esta@gmail.com"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_app_password)
            server.send_message(msg)
        st.success("📬 Test email sent successfully!")
    except Exception as e:
        st.error(f"Failed to send test email: {e}")

    # === Footer ===
    st.markdown("""
        <div style='text-align: center; padding-top: 2em;'>
            📩 Contact us: <a href='mailto:datacleanpro2025@gmail.com'>admin@datacleanpro.com</a>
        </div>
    """, unsafe_allow_html=True)