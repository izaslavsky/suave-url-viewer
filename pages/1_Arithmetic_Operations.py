import streamlit as st
import pandas as pd
import requests
import io
from urllib.parse import urlencode, urlparse
from datetime import datetime
import logging
from io import StringIO

# ---- Setup debug logging ----
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

log_stream = StringIO()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(log_stream)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)

# ---- Set Streamlit config ----
st.set_page_config(page_title="Arithmetic Operations", layout="wide")

# ---- Parse query parameters ----
query_params = st.query_params
user = query_params.get("user", None)
csv_filename = query_params.get("csv", None)
survey_url = query_params.get("surveyurl", None)
dzc_file = query_params.get("dzc", None)

# ---- Page Header ----
st.title("➕ Arithmetic Operations")
st.markdown("**Create new derived variables using arithmetic formulas, and publish back to SuAVE.**")

# ---- Input Info + Help ----
with st.expander("ℹ️ Help & Diagnostics", expanded=False):
    st.markdown("""
    - This tool allows you to add derived numeric variables to your dataset.
    - To publish your updated dataset to SuAVE, you must:
        1. Be logged into [SuAVE](https://suave-net.sdsc.edu) in the **same browser**.
        2. Open Developer Tools → Application → Cookies → `suave-net.sdsc.edu`
        3. Copy the value of the cookie named `connect.sid`
    """)
    st.markdown(f"🧪 Streamlit version: `{st.__version__}`")
    st.markdown(f"👤 User: `{user}`")
    st.markdown(f"📂 CSV File: `{csv_filename}`")

    if not csv_filename or not survey_url:
        st.error("❌ Missing CSV filename or survey URL. Use ?csv=...&surveyurl=... in the URL.")
        st.stop()

    parsed = urlparse(survey_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}/surveys/"
    csv_url = base_url + csv_filename
    st.markdown(f"🔗 Trying URL: `{csv_url}`")

    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        logger.exception("Failed to load CSV")
        st.error(f"❌ Could not fetch CSV: {e}")
        st.stop()

    df.columns = df.columns.str.strip()
    st.markdown("📋 **Column Check**")
    st.write(df.columns.tolist())
    st.write(df.dtypes.head())
    st.write(df.head(2))

# ---- Define new variable ----
st.markdown("---")
st.subheader("🧮 Define a New Derived Variable")

numeric_cols = df.select_dtypes(include='number').columns.tolist()
col1 = st.selectbox("➕ First Operand", numeric_cols)
operation = st.selectbox("⚙️ Operation", ["+", "-", "*", "/"])
col2 = st.selectbox("➕ Second Operand", numeric_cols)
new_var_base = st.text_input("📝 Name for the New Variable", value="new_var")
new_var = new_var_base + " #number"

if st.button("▶️ Compute"):
    try:
        if operation == "+":
            df[new_var] = df[col1] + df[col2]
        elif operation == "-":
            df[new_var] = df[col1] - df[col2]
        elif operation == "*":
            df[new_var] = df[col1] * df[col2]
        elif operation == "/":
            df[new_var] = df[col1] / df[col2]

        df[new_var] = df[new_var].where(df[new_var].notna(), '')
        st.success(f"✅ New column '{new_var}' added.")
        st.dataframe(df[[col1, col2, new_var]].head())
    except Exception as e:
        logger.exception("Computation error")
        st.error(f"❌ Error computing new variable: {e}")

# ---- Upload section ----
st.markdown("---")
st.subheader("📤 Publish to SuAVE")

cookie_sid = st.text_input("🔑 Paste your `connect.sid` cookie value from SuAVE:")

base_name = csv_filename.replace(".csv", "").split("_", 1)[-1]
suggested_name = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
survey_name = st.text_input("📛 Name for New Survey:", value=suggested_name)

if st.button("📦 Upload to SuAVE"):
    if not cookie_sid or not survey_name:
        st.warning("⚠️ Please provide both the cookie and survey name.")
    else:
        try:
            referer = survey_url.split("/main")[0] + "/"
            upload_url = referer + "uploadCSV"

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            s = requests.Session()
            s.cookies.set("connect.sid", cookie_sid, domain="suave-net.sdsc.edu")

            files = {
                "file": (f"{survey_name}.csv", csv_buffer.getvalue())
            }
            data = {
                "name": survey_name,
                "user": user
            }
            if dzc_file:
                data["dzc"] = dzc_file

            headers = {
                "User-Agent": "suave user agent",
                "referer": referer
            }

            upload_response = s.post(upload_url, files=files, data=data, headers=headers)

            logger.debug(f"Upload response code: {upload_response.status_code}")
            logger.debug(f"Upload response body: {upload_response.text}")

            if upload_response.status_code == 200:
                new_url = f"{referer}main/file={user}_{survey_name}.csv"
                st.success("✅ Survey uploaded successfully!")
                st.markdown(f"🔗 [Open New Survey in SuAVE]({new_url})")
            else:
                st.error(f"❌ Upload failed ({upload_response.status_code} — {upload_response.reason}). Please ensure you're logged in.")
                st.markdown("🔍 **Server Response:**")
                st.code(upload_response.text)
        except Exception as e:
            logger.exception("Upload exception")
            st.error(f"❌ Failed to upload: {e}")

# ---- Return to Home ----
param_str = urlencode({k: v[0] if isinstance(v, list) else v for k, v in query_params.items()})
st.markdown("""
<style>
.back-button {
    display: inline-block;
    padding: 0.6em 1.2em;
    margin-top: 2em;
    font-size: 1.1em;
    font-weight: bold;
    color: white !important;
    background-color: #1f77b4;
    border: none;
    border-radius: 8px;
    text-decoration: none;
}
.back-button:hover {
    background-color: #16699b;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown(f'<a href="/?{param_str}" class="back-button">⬅️ Return to Home</a>', unsafe_allow_html=True)

# ---- Show Debug Log ----
with st.expander("🪵 Debug Log"):
    log_stream.seek(0)
    st.code(log_stream.read(), language="text")
