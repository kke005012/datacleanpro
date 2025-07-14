# --- app.py ---
import streamlit as st
import pandas as pd
import gspread
import matplotlib.pyplot as plt
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO

from cleaner import (
    clean_data,
    strip_whitespace,
    drop_empty_rows,
    deduplicate,
    write_log
)
from cleaner import (
    standardize_column_names,
    clean_currency_columns,
    normalize_dates,
    handle_missing_values,
    final_sanity_check
)
from pricing import calculate_price

st.set_page_config(page_title="DataCleanPro", layout="wide")

# Navigation
page = st.sidebar.selectbox("📂 Choose a page", ["Welcome", "Clean My Data"])

if page == "Welcome":
    st.title("✨ Welcome to DataCleanPro")
    st.markdown("""
    **Clean data shouldn’t come with a dirty price tag.**  
    Pay only for what you clean — no subscriptions, no upsells, no tricks.

    ### ✅ What We Offer
    - Upload your messy CSV
    - Strip whitespace, fix formats, remove duplicates
    - Optional Pro features: fill missing data, download enhanced logs

    ### 💸 Pricing
    - First 100 rows:<strong>Free</strong><br>
    - After that:<br>
    &nbsp;&nbsp;&nbsp;&nbsp;<strong>$0.01 per 1000 rows up to 5000</strong><br>
    &nbsp;&nbsp;&nbsp;&nbsp;<strong>$0.008 per 1000 rows from 5001 to 25000</strong><br>
    &nbsp;&nbsp;&nbsp;&nbsp;<strong>$0.005 per 1000 rows from 25001 to 100000</strong><br>
    &nbsp;&nbsp;&nbsp;&nbsp;<strong>Please contact us for custom pricing beyond 100000 rows.</strong><br>
    - No commitments. No hidden fees.
    

    ### 📨 Need Help?
    Email us anytime: [datacleanpro2025@gmail.com](mailto:datacleanpro2025@gmail.com)

    :point_right: Use the sidebar to switch to **Clean My Data**
    """, unsafe_allow_html=True)

elif page == "Clean My Data":
    st.title("🧼 DataCleanPro: Clean Your CSV with Ease")

    st.markdown("""
    > :gear: **Before uploading a file, be sure to review the options in the sidebar to tailor how missing values are handled.**
    """)



    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    def validate_pro_code(user_code):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            client = gspread.authorize(creds)
            sheet = client.open("DataCleanPro Access Codes").sheet1
            codes = sheet.col_values(1)
            is_valid = user_code.strip() in codes

            if is_valid:
                try:
                    log_sheet = client.open("DataCleanPro Access Codes").worksheet("UsageLog")
                except:
                    log_sheet = client.open("DataCleanPro Access Codes").add_worksheet(title="UsageLog", rows="1000", cols="3")
                log_sheet.append_row([user_code.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), uploaded_file.name if uploaded_file else "-"])

            return is_valid
        except Exception as e:
            st.warning(f"Unable to validate Pro access: {e}")
            return False

    with st.sidebar:
        st.markdown("""
        <style>
            section[data-testid="stSidebar"] > div:first-child {
                background-color: #f0fdf4;
                padding: 20px;
                border-radius: 10px;
            }
            .sidebar-title {
                font-size: 22px;
                font-weight: bold;
                color: #66bb6a;
                margin-bottom: 10px;
            }
            .sidebar-section {
                padding-bottom: 10px;
                color: #388e3c;
            }
            .stRadio > label {
                color: #2e7d32;
            }
            .stDownloadButton > button {
                background-color: #66bb6a !important;
                color: white !important;
                border-radius: 8px !important;
                padding: 0.6em 1.2em !important;
                margin-top: 10px;
            }
            .stDownloadButton > button:hover {
                background-color: #5aaa59 !important;
            }
        </style>
        <div class='sidebar-title'>🧰 Cleaning Options</div>
        """, unsafe_allow_html=True)

        access_code = st.text_input("🔐 Enter Pro Access Code (for paid features)", type="password")
        is_paid_user = validate_pro_code(access_code)

        fill_missing = "No"
        fill_with_mode = None

        if is_paid_user:
            st.markdown("<div class='sidebar-section'>Choose how to handle missing values:</div>", unsafe_allow_html=True)
            fill_missing = st.radio("Handle Missing Values?", ["No", "Yes"], index=0)
            if fill_missing == "Yes":
                st.markdown("<div class='sidebar-section'>Select how to fill text-based (object) columns:</div>", unsafe_allow_html=True)
                fill_strategy = st.radio("Fill Object Columns With:", ["Unknown", "Mode"], index=0)
                st.markdown("<small>ℹ️ 'Mode' refers to the most frequently occurring value in a column.</small>", unsafe_allow_html=True)
                fill_with_mode = (fill_strategy == "Mode")
        else:
            st.markdown("⚠️ Upgrade to Pro to handle missing values.", unsafe_allow_html=True)

        with st.expander("💸 Pricing Details"):
            st.markdown("""
            - First 100 rows: **Free**  
            - After that:  
            &nbsp;&nbsp;&nbsp;&nbsp;**$0.01 per 1,000 rows up to 5,000**  \\
            &nbsp;&nbsp;&nbsp;&nbsp;**$0.008 per 1,000 rows from 5,001 to 25,000**  \\
            &nbsp;&nbsp;&nbsp;&nbsp;**$0.005 per 1,000 rows from 25,001 to 100,000**  \\
            &nbsp;&nbsp;&nbsp;&nbsp;**Custom pricing beyond 100,000 rows**  
            """)


        st.markdown("<hr><small>Need help? Contact us anytime: [datacleanpro2025@gmail.com](mailto:datacleanpro2025@gmail.com)</small>", unsafe_allow_html=True)

        if not is_paid_user:
            st.markdown("""
            <div style='border: 1px solid #66bb6a; background-color: #f9fff9; padding: 15px; border-radius: 10px;'>
            <strong>💡 Upgrade to DataCleanPro Pro</strong><br>
            Want to fill missing values, generate full reports, and access exclusive tools?<br>
            Get your Pro access code today by contacting us at 
            <a href="mailto:datacleanpro2025@gmail.com">datacleanpro2025@gmail.com</a>
            </div>
            """, unsafe_allow_html=True)

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df_before = df.copy(deep=True)

            st.info(f"📊 Dataset contains **{df.shape[0]} rows** and **{df.shape[1]} columns**.")

            st.subheader("📈 Column Type Distribution")
            col_types = df.dtypes.value_counts()
            fig, ax = plt.subplots()
            ax.pie(col_types.values, labels=col_types.index.astype(str), autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)

            with st.spinner("Cleaning in progress..."):
                log_lines = []
                df = standardize_column_names(df)
                df = clean_currency_columns(df, log_lines)
                df = normalize_dates(df, log_lines)
                if fill_missing == "Yes" and is_paid_user:
                    df = handle_missing_values(df, fill_with_mode, log_lines)
                df = final_sanity_check(df, log_lines)
                df = clean_data(df, log_lines)
                log_filename = write_log(log_lines)

            st.success("✅ Cleaning completed!")

            st.subheader("🔍 Cleaned Preview")
            st.dataframe(df.head())

            total_rows_cleaned = df.shape[0]
            cost, total_rows, billable_rows = calculate_price(total_rows_cleaned)

            if cost == 'custom':
                st.warning(f"✅ Cleaned {total_rows} rows.\n\n⚠️ For more than 100,000 rows, contact us at [datacleanpro2025@gmail.com](mailto:datacleanpro2025@gmail.com)")
                show_downloads = True
            else:
                st.info(f"✅ Cleaned {total_rows} rows ({billable_rows} billable)\n\n💵 Total cost: ${cost:.2f}")
                user_email = st.text_input("📧 Enter your email to receive a receipt or payment link:")
                show_downloads = user_email.strip() != ""
                if not show_downloads:
                    st.warning("⚠️ Please enter your email to proceed with download.")

            if show_downloads:
                csv_download = df.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download Cleaned CSV", data=csv_download, file_name="cleaned_data.csv", mime="text/csv")

                with open(log_filename, "rb") as f:
                    st.download_button("📝 Download Cleaning Log", data=f, file_name=log_filename, mime="text/plain")

            if not is_paid_user:
                st.info("Want to fix missing values and unlock detailed reports? Upgrade to DataCleanPro Pro!")

        except Exception as e:
            st.error(f"❌ Cleaning failed: {e}")
