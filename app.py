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
""", unsafe_allow_html=True)

    st.markdown("""
<h4><span>&#x1F4B8;</span> Pricing</h4>
<p><strong>First 100 rows: Free</strong></p>
<p><strong>After that:</strong></p>
<ul style="list-style-type: none; padding-left: 1em;">
  <li><strong>$0.02 per row from 101 to 500</strong></li>
  <li><strong>$0.015 per row from 501 to 1500</strong></li>
  <li><strong>$0.01 per row from 1501 to 10,000</strong></li>
  <li><strong>$0.008 per row from 10001 to 25000</strong></li>
  <li><strong>$0.007 per row from 25001 to 100,000</strong></li>
  <li><strong>Please contact us for custom pricing beyond "100,000" rows.</strong></li>
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

    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("File uploaded successfully!")
            st.write("### 📊 Preview of Uploaded Data")
            st.dataframe(df.head())

            # Radio buttons for missing value handling
            st.write("### 🛠️ Missing Value Handling")
            numeric_strategy = st.radio(
                "Missing Numeric Values:",
                ["Ignore", "Replace with Unknown", "Use Average ℹ️"],
                index=0,
                help="Choose how to handle missing numeric values."
            )

            non_numeric_strategy = st.radio(
                "Missing Non-Numeric Values:",
                ["Ignore", "Replace with Unknown", "Use Mode ℹ️"],
                index=0,
                help="Choose how to handle missing text or categorical values."
            )

            # Map choices to internal codes
            numeric_map = {
                "Ignore": "ignore",
                "Replace with Unknown": "unknown",
                "Use Average ℹ️": "average"
            }
            non_numeric_map = {
                "Ignore": "ignore",
                "Replace with Unknown": "unknown",
                "Use Mode ℹ️": "mode"
            }

            if st.button("Clean My Data"):
                cleaned_df = clean_data(df, numeric_map[numeric_strategy], non_numeric_map[non_numeric_strategy])
                st.write("### ✅ Cleaned Data Preview")
                st.dataframe(cleaned_df.head())

                if st.checkbox("Show cleaning log"):
                    st.write("### 📋 Cleaning Log")
                    for line in write_log(df, cleaned_df):
                        st.markdown(f"- {line}")

                st.download_button("📥 Download Cleaned CSV", data=cleaned_df.to_csv(index=False), file_name="cleaned_data.csv")

        except Exception as e:
            st.error(f"⚠️ An error occurred while processing the file: {e}")

    # Footer contact info
    st.markdown("""
        <div style='text-align: center; padding-top: 2em;'>
            📩 Contact us: <a href='mailto:datacleanpro2025@gmail.com'>datacleanpro2025@gmail.com</a>
        </div>
    """, unsafe_allow_html=True)