import streamlit as st
import pandas as pd
import requests
import io
import logging
from urllib.parse import urlencode, urlparse
from datetime import datetime

st.set_page_config(page_title="Arithmetic Operations", layout="wide")

# ---- Initialize logging ----
from io import StringIO
log_stream = StringIO()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(log_stream)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

# ---- Read query params from URL ----
query_params = st.query_params
user = query_params.get("user", None)
csv_filename = query_params.get("csv", None)
survey_url = query_params.get("surveyurl", None)
dzc_file = query_params.get("dzc", None)

# ---- Page title and description ----
st.title("➕ Arithmetic Operations")
st.markdown("**Create new derived variables using arithmetic formulas, and publish back to SuAVE.**")

# ---- Collapsible diagnostics ----
with st.expander("⚙️ Diagnostics and Input Info", expanded=False):
    st.markdown(f"🧪 <span style='font-size: 0.85em;'>**Streamlit version:** {st.__version__}</span>", unsafe_allow_html=True)
    st.markdown(f"👤 <span style='font-size: 0.85em;'>**User:** {user}</span>", unsafe_allow_html=True)
    st.markdown(f"📂 <span style='font-size: 0.85em;'>**CSV File:** {csv_filename}</span>", unsafe_allow_html=True)

    if not csv_filename or not survey_url:
        st.error("❌ Missing CSV filename or survey URL. Use ?csv=...&surveyurl=... in the URL.")
        st.stop()

    parsed = urlparse(survey_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}/surveys/"
    csv_url = base_url + csv_filename
    st.markdown(f"🔗 <span style='font-size: 0.85em;'>Trying URL: {csv_url}</span>", unsafe_allow_html=True)

    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        st.error(f"❌ Could not fetch CSV: {e}")
        st.stop()

    st.markdown("<span style='font-size: 0.9em;'>📋 Column Check</span>", unsafe_allow_html=True)
    df.columns = df.columns.str.strip()
    st.write(df.columns.tolist())
    st.write(df.dtypes.head())
    st.write(df.head(2))

# ---- Define operation ----
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
        st.error(f"❌ Error computing new variable: {e}")

# ---- Help & Publish section ----
st.markdown("---")
st.subheader("📤 Publish Back to SuAVE")

st.info("""
To upload your result back to SuAVE, you **must be logged in to [https://suave-net.sdsc.edu](https://suave-net.sdsc.edu)** in the same browser.

If your session is not recognized, paste your `connect.sid` cookie below:

**To find your cookie:**
1. Visit [https://suave-net.sdsc.edu](https://suave-net.sdsc.edu) and log in.
2. Press `F12` or `Right Click → Inspect`.
3. Go to the **Application** tab → **Cookies** → `suave-net.sdsc.edu`.
4. Copy the **entire value** of the cookie named `connect.sid`.
""")

sid_cookie = st.text_input("🍪 Paste your `connect.sid` cookie here:")

base_name = csv_filename.replace(".csv", "").split("_", 1)[-1]
suggested_name = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
survey_name = st.text_input("📛 Name for New Survey:", value=suggested_name)

if st.button("📦 Upload to SuAVE"):
    if not sid_cookie or not survey_name:
        st.warning("⚠️ Please provide both cookie and survey name.")
    else:
        try:
            parsed = urlparse(survey_url)
            referer = f"{parsed.scheme}://{parsed.netloc}/"
            upload_url = referer + "uploadCSV"

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            s = requests.Session()
            s.cookies.set("connect.sid", sid_cookie, domain=parsed.netloc)
            headers = {
                "User-Agent": "suave user agent",
                "referer": referer
            }

            files = {
                "file": (f"{survey_name}.csv", csv_buffer.getvalue())
            }
            data = {
                "name": survey_name,
                "user": user
            }
            if dzc_file:
                data["dzc"] = dzc_file

            logger.debug(f"Uploading to: {upload_url}")
            logger.debug(f"Survey name: {survey_name}")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Data: {data}")
            logger.debug(f"Cookies: {s.cookies.get_dict()}")

            upload_response = s.post(upload_url, files=files, data=data, headers=headers)

            logger.debug(f"Status Code: {upload_response.status_code}")
            logger.debug(f"Response Text: {upload_response.text}")

            if upload_response.status_code == 200:
                new_survey_url = f"{referer}main/file={user}_{survey_name}.csv"
                st.success("✅ Survey uploaded successfully!")
                st.markdown(f"🔗 [Open New Survey in SuAVE]({new_survey_url})")
            else:
                st.error(f"❌ Upload failed ({upload_response.status_code} — {upload_response.reason}). Please ensure you're logged in.")
                st.markdown("### 🔍 Server Response:")
                st.code(upload_response.text)
        except Exception as e:
            logger.exception("Upload failed due to exception")
            st.error(f"❌ Upload failed: {e}")

# ---- Debug Log ----
st.markdown("### 🪵 Debug Log")
st.code(log_stream.getvalue())

# ---- Return to Home button ----
param_str = urlencode({k: v[0] if isinstance(v, list) else v for k, v in query_params.items()})
button_css = """
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
"""
st.markdown(button_css, unsafe_allow_html=True)
st.markdown(f'<a href="/?{param_str}" class="back-button">⬅️ Return to Home</a>', unsafe_allow_html=True)
