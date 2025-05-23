import streamlit as st
import pandas as pd
import requests
import io
from urllib.parse import urlencode, urlparse
from datetime import datetime

# ---- Page Setup ----
st.set_page_config(page_title="Arithmetic Operations", layout="wide")

# ---- Logging Infrastructure ----
debug_log = []
def log(msg):
    debug_log.append(msg)

# ---- Read query params from URL ----
query_params = st.query_params
user = query_params.get("user", None)
csv_filename = query_params.get("csv", None)
survey_url = query_params.get("surveyurl", None)
dzc_file = query_params.get("dzc", None)

# ---- Page Title ----
st.title("➕ Arithmetic Operations")
st.markdown("**Create new derived variables using arithmetic formulas, and publish back to SuAVE.**")

# ---- Help Section for Session Cookie ----
with st.expander("❓ How to get your session cookie"):
    st.markdown("""
    To publish your new dataset to SuAVE, you must be logged in to https://suave-net.sdsc.edu/ **in the same browser**.

    Then follow these steps:

    1. Open [https://suave-net.sdsc.edu/](https://suave-net.sdsc.edu/) and log in.
    2. Press **F12** (or right-click → **Inspect**) to open **Developer Tools**.
    3. Go to the **Application** tab → **Cookies** → `https://suave-net.sdsc.edu`.
    4. Find the cookie named `connect.sid` and **copy its full value**.
    5. Paste it below to allow publishing.

    Example: `s:abc123xyz...`  
    You **must paste the decoded version** (not `%2F` etc.).
    """)

# ---- Collapsible Diagnostics ----
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

    df.columns = df.columns.str.strip()
    st.markdown("📋 **Columns:**")
    st.write(df.columns.tolist())

# ---- Select Columns and Operation ----
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

# ---- Save and Upload ----
st.markdown("---")
st.subheader("📤 Publish Back to SuAVE")

session_cookie = st.text_input("🔐 Paste your `connect.sid` session cookie (decoded format):")

base_name = csv_filename.replace(".csv", "").split("_", 1)[-1]
suggested_name = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
survey_name = st.text_input("📛 Name for New Survey:", value=suggested_name)

if st.button("📦 Upload to SuAVE"):
    if not session_cookie or not survey_name:
        st.warning("⚠️ Please fill in both the session cookie and survey name.")
    else:
        try:
            parsed = urlparse(survey_url)
            referer = survey_url.split("/main")[0] + "/"
            upload_url = referer + "uploadCSV"

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            log("Preparing session and headers")
            s = requests.Session()
            s.cookies.update({ "connect.sid": session_cookie })
            s.headers.update({
                "User-Agent": "suave user agent",
                "referer": referer,
                "Cookie": f"connect.sid={session_cookie}"
            })

            log("Sending POST to uploadCSV")
            files = {
                "file": (f"{survey_name}.csv", csv_buffer.getvalue())
            }
            data = {
                "name": survey_name,
                "user": user
            }
            if dzc_file:
                data["dzc"] = dzc_file

            upload_response = s.post(upload_url, files=files, data=data, headers=headers)

            log(f"Status: {upload_response.status_code}")
            log(f"Response text: {upload_response.text}")

            if upload_response.status_code == 200:
                new_survey_url = f"{referer}main/file={user}_{survey_name}.csv"
                st.success("✅ Survey uploaded successfully!")
                st.markdown(f"🔗 [Open New Survey in SuAVE]({new_survey_url})")
            else:
                st.error(f"❌ Upload failed ({upload_response.status_code} — {upload_response.reason}). Please ensure you're logged in.")
                st.markdown("🔍 **Server Response:**")
                st.code(upload_response.text)
        except Exception as e:
            log(f"Exception: {e}")
            st.error(f"❌ Upload failed due to error: {e}")

# ---- Return to Home Button ----
param_str = urlencode({k: v[0] if isinstance(v, list) else v for k, v in query_params.items()})
button_css = """
<style>
.back-button {
    display: inline-block;
    padding: 0.6em  1.2em;
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

# ---- Render Debug Log ----
if debug_log:
    st.markdown("---")
    st.subheader("🪵 Debug Log")
    st.code("\n".join(debug_log), language="text")
