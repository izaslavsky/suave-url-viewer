import streamlit as st
st.set_page_config(page_title="Arithmetic Operations", layout="wide")

import pandas as pd
import requests
import io
from urllib.parse import urlencode, urlparse
from datetime import datetime

# --- Read query params ---
query_params = st.query_params
user = query_params.get("user", None)
csv_filename = query_params.get("csv", None)
survey_url = query_params.get("surveyurl", None)
dzc_file = query_params.get("dzc", None)

# --- Title and intro ---
st.title("➕ Arithmetic Operations")
st.markdown("**Create derived variables using arithmetic formulas and publish to SuAVE.**")
st.markdown("Before publishing, please log into [SuAVE](https://suave-net.sdsc.edu/) in this browser and copy your session cookie (`JSESSIONID`).")

# --- Diagnostics (collapsible) ---
with st.expander("⚙️ Diagnostics", expanded=False):
    st.markdown(f"🔧 **Streamlit version:** `{st.__version__}`")
    st.markdown(f"👤 **User:** `{user}`")
    st.markdown(f"📁 **CSV File:** `{csv_filename}`")

    if not csv_filename or not survey_url:
        st.error("❌ Missing ?csv=... or ?surveyurl=... in URL.")
        st.stop()

    parsed = urlparse(survey_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}/surveys/"
    csv_url = base_url + csv_filename
    st.markdown(f"🔗 Attempting to load: `{csv_url}`")

    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        st.error(f"❌ Failed to load CSV: {e}")
        st.stop()

    st.markdown("### Columns:")
    df.columns = df.columns.str.strip()
    st.write(df.columns.tolist())
    st.write(df.dtypes.head())
    st.write(df.head(2))

# --- Define arithmetic operation ---
st.markdown("---")
st.subheader("🧮 Create a New Variable")

numeric_cols = df.select_dtypes(include='number').columns.tolist()
col1 = st.selectbox("➕ First Operand", numeric_cols)
operation = st.selectbox("⚙️ Operation", ["+", "-", "*", "/"])
col2 = st.selectbox("➕ Second Operand", numeric_cols)
new_var_base = st.text_input("📛 Name for New Variable", value="new_var")
new_var = new_var_base + " #number"

if st.button("▶️ Compute"):
    try:
        if operation == "+": df[new_var] = df[col1] + df[col2]
        elif operation == "-": df[new_var] = df[col1] - df[col2]
        elif operation == "*": df[new_var] = df[col1] * df[col2]
        elif operation == "/": df[new_var] = df[col1] / df[col2]
        df[new_var] = df[new_var].where(df[new_var].notna(), '')
        st.success(f"✅ New column `{new_var}` added.")
        st.dataframe(df[[col1, col2, new_var]].head())
    except Exception as e:
        st.error(f"❌ Error computing variable: {e}")

# --- Publish section ---
st.markdown("---")
st.subheader("📤 Publish to SuAVE")

# Survey name suggestion
base_name = csv_filename.replace(".csv", "").split("_", 1)[-1]
suggested_name = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
survey_name = st.text_input("📝 Name for New Survey", value=suggested_name)

# Cookie for authentication
session_id = st.text_input("🔐 Paste your JSESSIONID from suave-net.sdsc.edu cookies:", type="password")

# Upload
if st.button("📦 Upload"):
    if not survey_name or not session_id:
        st.warning("⚠️ Please provide a survey name and your SuAVE session ID.")
    else:
        try:
            referer = survey_url.split("/main")[0] + "/"
            upload_url = referer + "uploadCSV"

            # Prepare data
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            # Prepare session
            s = requests.Session()
            s.cookies.set("JSESSIONID", session_id)

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

            upload_response = s.post(upload_url, files=files, data=data, headers=headers)

            if upload_response.status_code == 200:
                new_url = f"{referer}main/file={user}_{survey_name}.csv"
                st.success("✅ Survey uploaded successfully!")
                st.markdown(f"🔗 [Open new survey in SuAVE]({new_url})")
            else:
                st.error(f"❌ Upload failed ({upload_response.status_code} — {upload_response.reason})")
                st.markdown("🔍 **Server Response:**")
                st.code(upload_response.text, language="text")

        except Exception as e:
            st.error(f"❌ Upload exception: {e}")

# --- Home button ---
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
}
</style>
""", unsafe_allow_html=True)
st.markdown(f'<a href="/?{param_str}" class="back-button">⬅️ Return to Home</a>', unsafe_allow_html=True)
