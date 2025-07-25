# === app.py ===
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
    handle_missing_values
)
from pricing import calculate_price

def logger(*args):
    st.write(*args)

st.set_page_config(page_title="DataClean Pro | Clean Real-World CSVs Fast", page_icon="🧼", layout="wide")

# Navigation
page = st.sidebar.selectbox("📂 Choose a page", ["Welcome", "Clean My Data"])

st.sidebar.markdown(
    """
    <hr style='margin-top: 1.5rem; margin-bottom: 0.5rem'>
    <div style='font-size: 0.75rem; color: gray; text-align: center;'>
        🧼 DataClean Pro is a cloud-based cleaning service for real-world CSVs.
    </div>
    """,
    unsafe_allow_html=True
)

if page == "Welcome":
    st.markdown("""
    ### Welcome to DataCleanPro 🧼  
    DataCleanPro is a cloud-based data cleaning tool designed for real-world CSV files.  
    Whether you're dealing with missing values, inconsistent dates, or currency formatting, we've got you covered.

    Clean your dataset, download your results, and get back to real work — fast.
    """)

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
<p><strong>100 rows or less: Free</strong></p>
<p><strong>After that:</strong></p>
<ul style="list-style-type: none; padding-left: 1em;">
  <li><strong>$0.02 per row up to 500</strong></li>
  <li><strong>$0.015 per row up to 1500</strong></li>
  <li><strong>$0.01 per row up to 10,000</strong></li>
  <li><strong>$0.008 per row up to 25,000</strong></li>
  <li><strong>$0.007 per row up to 100,000</strong></li>
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
    non_num_missing_placeholder = ""
    num_missing_placeholder = ""
    if "raw_df" in st.session_state and st.session_state.raw_df is not None:
        with st.sidebar:
            st.sidebar.markdown("### 🧹 Cleaning Options")

            keep_dollar = st.sidebar.checkbox("Keep '$' sign in currency?", value=False, help="Assumes USD format with period as decimal separator.")
            display_map = {"NULL": "null", "NaN": "NaN"}
            #missing_values_option = st.radio(
                #"Preferred placeholder for missing values:",
                #options=["NULL", "NaN"],
                #format_func=lambda x: display_map[x],
                #index=0,
                #key="missing values"
            #)

            st.sidebar.markdown("**Missing Value Filler**")
            numeric_strategy = st.sidebar.radio(
                "Numeric Columns",
                options=["Ignore", "Unknown", "Average"],
                index=0,
                key="missing numeric"
            )
            if numeric_strategy == "Unknown":
                num_missing_placeholder = st.radio("Preferred Numeric Filler:", ["null", "NaN"])
            
            non_numeric_strategy = st.sidebar.radio(
                "Text Columns",
                options=["Ignore", "Unknown", "Mode"],
                index=0,
                key="missing non-numeric"
            )
            if non_numeric_strategy == "Unknown":
                non_num_missing_placeholder = st.radio("Preferred Text Filler:", ["null", "NaN"])

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
                    "[contact us](mailto:datacleanpro2025@gmail.com) (datacleanpro2025@gmail.com) for a custom order/pricing.",
                    icon="🚫"
                )
                st.stop()
            if (len(df) == 1 and has_header) or (len(df) == 0 and not has_header):
                st.error(
                    "❌ This app supports a minimum of 1 row of data. Please refresh and try again with a data file."
                )
                st.stop()
            # ==== End Row Count Check ===                    
 
            st.session_state.raw_df = df.copy()
            logger(f"##DEBUG: About to clean {len(st.session_state.raw_df)} rows.")
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

            # === Clean button only appears if data is ready ===

            if st.button("Clean My Data"):
                logger(f"##DEBUG Clean My Data Button.")
                
                logger(f"##DEBUG: session state raw_df", st.session_state.raw_df.head())
                 
                cleaned_df = clean_data(
                    st.session_state.raw_df.copy(),
                    keep_dollar=keep_dollar,
                    missing_values_option=missing_values_option,
                    numeric_strategy=numeric_map[numeric_strategy],
                    non_numeric_strategy=non_numeric_map[non_numeric_strategy],
                    num_missing_placeholder=num_missing_placeholder,
                    non_num_missing_placeholder=non_num_missing_placeholder,
                    logger = st.write if debug_mode else None,
                    has_header=has_header
                )

                logger(f"##DEBUG: Cleaned {len(cleaned_df)} rows.")
                st.session_state.cleaned_df = cleaned_df
                st.session_state["cleaning_log"] = cleaned_df.attrs["log"]

                logger(f"##DEBUG: cleaned_df", cleaned_df.head())
                logger(f"##DEBUG: session state cleaned_df", st.session_state.cleaned_df.head())
                logger(f"##DEBUG: session state raw_df", st.session_state.raw_df.head())

        elif st.session_state.upload_attempted:
            st.warning(" ⚠️ No raw data available to clean. Please upload a file.")

        # === Show cleaned data ===
        cleaned_df = st.session_state.get("cleaned_df", None)
        
        if cleaned_df is not None and not cleaned_df.empty:
            logger(f"##DEBUG: if cleaned_df is not None and not cleaned_df.empty")
            st.write("### ✅ Cleaned Data Preview")
            st.dataframe(cleaned_df.head())
            rows, cols = cleaned_df.shape
            logger(f"##DEBUG: cleaned data preview — {rows} rows × {cols} columns")

     
            row_count = len(cleaned_df)
            cost, rows = calculate_price(row_count)
            logger(f"##DEBUG: after pricing call, cost={cost} rows={rows}")

            st.session_state["row_count"] = row_count
            st.session_state["cost"] = cost
            st.session_state["total_rows"] = rows
            logger(f"##DEBUG: cost in session_state = {st.session_state.get('cost')}")
            if "cost" in st.session_state and "total_rows" in st.session_state:
                st.markdown(f"**Standard Cost: ${st.session_state['cost']:.2f}**. Total Rows = {st.session_state['total_rows']}.")

            if row_count > 100:
                st.warning(f"Your file has {row_count} rows.")

                user_email = st.text_input("📧 Enter your email to receive a receipt with cleaning details")

                if user_email:
                    st.success("✅ Email captured. Proceed to payment below.")

                if user_email and st.button("💳 Proceed to Payment (Mock)"):
                    st.session_state.payment_complete = True
                    st.session_state.customer_email = user_email
                    st.success("💰 Payment successful (mock)!")

            if st.checkbox("Show cleaning log"):
                logger(f"##DEBUG: in Show Cleaning Log if statement")
                st.write("### 📋 Cleaning Log")
                log_lines = write_log(cleaned_df)
                if log_lines:
                    for line in log_lines:
                        st.markdown(f"- {line}")
                else:
                    st.info("No cleaning actions were logged.")

            st.download_button(
                " 📥 Download Cleaned CSV",
                data=cleaned_df.to_csv(index=False),
                file_name=download_filename,
                mime="text/csv"
            )

            if st.session_state.get("payment_complete", False):
                cleaned_df = st.session_state.cleaned_df
                if cleaned_df is not None:
                    st.download_button(
                    " 📥 Download Cleaned CSV",
                    data=cleaned_df.to_csv(index=False),
                    file_name=download_filename if uploaded_file else "cleaned_data.csv"
            )

        if st.button("📧 View Simulated Email Receipt"):
            cleaning_log = write_log(st.session_state.raw_df, cleaned_df)
            receipt = f"""
            **Receipt for {st.session_state.customer_email}**

            ✅ Rows cleaned: {len(cleaned_df)}
            💵 Amount Paid: ${cost:.2f}

            🧹 Cleaning Actions:
            """
            for line in cleaning_log:
                receipt += f"\n- {line}"

            st.markdown(receipt)


    # === Footer ===
    st.markdown("""
        <div style='text-align: center; padding-top: 2em;'>
            📩 Contact us: <a href='mailto:datacleanpro2025@gmail.com'>datacleanpro2025@gmail.com</a>
        </div>
    """, unsafe_allow_html=True)