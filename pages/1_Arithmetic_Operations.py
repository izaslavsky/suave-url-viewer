import streamlit as st
st.set_page_config(page_title="Arithmetic Operations", layout="wide")

# ---- Import dependencies ----
import pandas as pd
import requests
import io
from urllib.parse import urlencode, urlparse
from datetime import datetime

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

# ---- Select columns and define operation ----
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
        df[new_var] = df[new_var].where(df[new_var].notna(), '')  # Blank for errors
        st.success(f"✅ New column '{new_var}' added.")
        st.dataframe(df[[col1, col2, new_var]].head())
    except Exception as e:
        st.error(f"❌ Error computing new variable: {e}")

# ---- Save and publish back ----
st.markdown("---")
st.subheader("📤 Publish Back to SuAVE")
auth_user = st.text_input("🔐 SuAVE Login:")
auth_token = st.text_input("🔑 API Token or Password:", type="password")

base_name = csv_filename.replace(".csv", "").split("_", 1)[-1]
suggested_name = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
survey_name = st.text_input("📛 Name for New Survey:", value=suggested_name)

if st.button("📦 Upload to SuAVE"):
    if not survey_name or not auth_user or not auth_token:
        st.warning("⚠️ Please fill in all fields before uploading.")
    else:
        try:
            parsed = urlparse(survey_url)
            referer = survey_url.split("/main")[0] + "/"
            upload_url = referer + "uploadCSV"

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            files = {
                "file": (f"{survey_name}.csv", csv_buffer.getvalue())
            }
            data = {
                "user": auth_user,
                "password": auth_token,
                "name": survey_name
            }
            if dzc_file:
                data["dzc"] = dzc_file

            headers = {
                "User-Agent": "suave user agent",
                "referer": referer
            }

            r = requests.post(upload_url, files=files, data=data, headers=headers)

            if r.status_code == 200:
                new_survey_url = f"{referer}main/file={auth_user}_{survey_name}.csv"
                st.success("✅ Survey uploaded successfully!")
                st.markdown(f"🔗 [Open New Survey in SuAVE]({new_survey_url})")
            elif r.status_code == 401:
                st.error("❌ Authentication failed. Please check your SuAVE credentials.")
            else:
                st.error(f"❌ Upload failed: {r.status_code} — {r.reason}")
        except Exception as e:
            st.error(f"❌ Failed to upload: {e}")

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
