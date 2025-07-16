# --- app.py ---
import streamlit as st
import pandas as pd
import gspread
import matplotlib.pyplot as plt
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
import hashlib

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
• Replace missing numeric/non-numeric values or leave as-is...your choice! 
""", unsafe_allow_html=True)

    st.markdown("""
<h4><span>&#x1F4B8;</span> Pricing</h4>
<p><strong>First 100 rows: Free</strong></p>
<p><strong>After that:</strong></p>
<ul style="list-style-type: none; padding-left: 1em;">
  <li><strong>$0.02 per row from 101 to 500</strong></li>
  <li><strong>$0.015 per row from 501 to 1500</strong></li>
  <li><strong>$0.01 per row from 1501 to 10,000</strong></li>
  <li><strong>$0.008 per row from 10,001 to 25,000</strong></li>
  <li><strong>$0.007 per row from 25,001 to 100,000</strong></li>
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
    import hashlib

    st.title("🧹 Clean My Data")

    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    # --- Safe session state initialization ---
    for key in ["raw_df", "cleaned_df", "file_hash"]:
        if key not in st.session_state:
            st.session_state[key] = None

    def get_file_hash(file):
        return hashlib.md5(file.getvalue()).hexdigest()

    # --- Load file into session state ---
    if uploaded_file is not None:
        file_hash = get_file_hash(uploaded_file)

        if st.session_state.file_hash != file_hash:
            df = pd.read_csv(uploaded_file)
            st.session_state.raw_df = df.copy()
            st.session_state.cleaned_df = None
            st.session_state.file_hash = file_hash
            st.success("File uploaded and loaded fresh!")
        else:
            st.info("Same file detected — using cached version.")

    # --- Show raw data preview if available ---
    if st.session_state.raw_df is not None:
        st.write("### 📊 Preview of Uploaded Data")
        st.dataframe(st.session_state.raw_df.head())

        # --- Cleaning Options ---
        st.markdown("""
        <div style='margin-top: 2em; text-align: center;'>
            <h4> 🛠️ Handle Missing Values</h4>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='display: flex; justify-content: center; flex-direction: column; align-items: center;'>
        """, unsafe_allow_html=True)

        numeric_strategy = st.radio(
            "Missing Numeric Values:",
            ["Ignore", "Replace with Unknown", "Use Average"],
            index=0
        )

        non_numeric_strategy = st.radio(
            "Missing Non-Numeric Values:",
            ["Ignore", "Replace with Unknown", "Use Mode"],
            index=0
        )

        st.markdown("</div>", unsafe_allow_html=True)

        numeric_map = {
            "Ignore": "ignore",
            "Replace with Unknown": "unknown",
            "Use Average": "average"
        }
        non_numeric_map = {
            "Ignore": "ignore",
            "Replace with Unknown": "unknown",
            "Use Mode": "mode"
        }

        # --- Clean button only appears if data is ready ---
        if st.button("Clean My Data"):
            cleaned_df = clean_data(
                st.session_state.raw_df.copy(),
                numeric_strategy=numeric_map[numeric_strategy],
                non_numeric_strategy=non_numeric_map[non_numeric_strategy]
            )
            st.session_state.cleaned_df = cleaned_df

            row_count = len(cleaned_df)
            cost = calculate_price(row_count)
            st.markdown(f"**Estimated Cost: ${cost:.2f}**")

    else:
        st.warning("⚠️ No raw data available to clean. Please upload a file.")

    # --- Show cleaned data ---
    if st.session_state.cleaned_df is not None:
        st.write("### ✅ Cleaned Data Preview")
        st.dataframe(st.session_state.cleaned_df.head())

        if st.checkbox("Show cleaning log"):
            st.write("### 📋 Cleaning Log")
            log_lines = write_log(st.session_state.raw_df, st.session_state.cleaned_df)
            if log_lines:
                for line in log_lines:
                    st.markdown(f"- {line}")
            else:
                st.info("No cleaning actions were logged.")

        st.download_button(
            "📥 Download Cleaned CSV",
            data=st.session_state.cleaned_df.to_csv(index=False),
            file_name="cleaned_data.csv"
        )

    # --- Reset button for dev use ---
    if st.button("🔄 Reset Session"):
        for key in ["raw_df", "cleaned_df", "file_hash"]:
            st.session_state[key] = None
        st.experimental_rerun()

    # --- Footer ---
    st.markdown("""
        <div style='text-align: center; padding-top: 2em;'>
            📩 Contact us: <a href='mailto:datacleanpro2025@gmail.com'>datacleanpro2025@gmail.com</a>
        </div>
    """, unsafe_allow_html=True)