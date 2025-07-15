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
    write_log,
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

#### ✅ What We Offer  
• Upload your messy CSV  
• Strip whitespace, fix formats, remove duplicates  
• Replace missing non-numeric values using Mode or Unknown

    st.markdown("""
<h4><span>&#x1F4B8;</span> Pricing</h4>
<p><strong>First 100 rows: Free</strong></p>
<p><strong>After that:</strong></p>
<ul style="list-style-type: none; padding-left: 1em;">
  <li><strong>$0.01 per 1,000 rows up to 5,000</strong></li>
  <li><strong>$0.008 per 1,000 rows from 5,001 to 25,000</strong></li>
  <li><strong>$0.005 per 1,000 rows from 25,001 to 100,000</strong></li>
  <li><strong>Please contact us for custom pricing beyond 100,000 rows.</strong></li>
</ul>
<p>No commitments. No hidden fees.</p>
""", unsafe_allow_html=True)

    st.markdown("""
#### 📨 Need Help?  
Email us anytime: [datacleanpro2025@gmail.com](mailto:datacleanpro2025@gmail.com)

#### 👉 Use the sidebar to switch to **Clean My Data**
""", unsafe_allow_html=True)

elif page == "Clean My Data":
    st.title("🧹 Clean My Data")

    uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

    handle_missing_flag = st.sidebar.checkbox("Handle missing values")
    show_log = st.sidebar.checkbox("Show cleaning log")

    try:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.subheader("🔍 Preview of Uploaded Data")
            st.dataframe(df.head())

            cleaned_df = clean_data(df, handle_missing_flag)

            st.subheader("✅ Cleaned Data Preview")
            st.dataframe(cleaned_df.head())

            cost, total_rows, billable_rows = calculate_price(len(df))

            st.markdown(f"**Total Rows:** {total_rows}")
            st.markdown(f"**Billable Rows:** {billable_rows}")

            if cost == 'custom':
                st.warning("For more than 100,000 rows, please contact us for a custom quote.")
            elif total_rows <= 100:
                st.success("🎉 This one's on us! Your file is under 100 rows.")
            else:
                st.success(f"💰 Your total cost is: **${cost:.2f}**")

            csv = cleaned_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Cleaned CSV",
                data=csv,
                file_name='cleaned_data.csv',
                mime='text/csv'
            )

            if show_log:
                st.subheader("🧾 Cleaning Log")
                log_lines = write_log(df, cleaned_df)
                for line in log_lines:
                    st.text(line)

                log_txt = "\n".join(log_lines).encode("utf-8")
                st.download_button(
                    label="📥 Download Cleaning Log",
                    data=log_txt,
                    file_name='cleaning_log.txt',
                    mime='text/plain'
                )
    except Exception as e:
        st.error(f"⚠️ An error occurred while processing the file: {str(e)}")