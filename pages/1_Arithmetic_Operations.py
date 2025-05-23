import streamlit as st
import pandas as pd
import requests
import io
from urllib.parse import urlencode, urlparse
from datetime import datetime

# -----------------------------
# Page config and header
# -----------------------------
st.set_page_config(page_title="Arithmetic Operations", layout="wide")
st.title("➕ Arithmetic Operations")
st.markdown("**Create new derived variables using arithmetic formulas, and publish back to SuAVE.**")

# -----------------------------
# Read query params
# -----------------------------
query_params = st.query_params
user = query_params.get("user", None)
csv_filename = query_params.get("csv", None)
survey_url = query_params.get("surveyurl", None)
dzc_file = query_params.get("dzc", None)

# -----------------------------
# Diagnostics and CSV loading
# -----------------------------
with st.expander("⚙️ Diagnostics and Input Info", expanded=False):
    st.markdown(f"🧪 **Streamlit version:** `{st.__version__}`")
    st.markdown(f"👤 **User:** `{user}`")
    st.markdown(f"📂 **CSV File:** `{csv_filename}`")
    st.markdown(f"🌐 **Survey URL:** `{survey_url}`")

    if not csv_filename or not survey_url:
        st.error("❌ Missing CSV filename or survey URL. Use ?csv=...&surveyurl=... in the URL.")
        st.stop()

    parsed = urlparse(survey_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}/surveys/"
    csv_url = base_url + csv_filename
    st.markdown(f"🔗 Trying to load: `{csv_url}`")

    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        st.error(f"❌ Could not fetch CSV: {e}")
        st.stop()

    st.markdown("📋 Column Check:")
    df.columns = df.columns.str.strip()
    st.write(df.columns.tolist())
    st.write(df.dtypes.head())
    st.write(df.head(2))

# -----------------------------
# Define new variable
# -----------------------------
st.markdown("---")
st.subheader("🧮 Define a New Derived Variable")

numeric_cols = df.select_dtypes(include='number').columns.tolist()
col1 = st.selectbox("➕ First Operand", numeric_cols)
operation = st.selectbox("⚙️ Operation", ["+", "-", "*", "/"])
col2 = st.selectbox("➕ Second Operand", numeric_cols)
new_var_base = st.text_input("📝 Name for the New Variable", value="new_var")
new_var = new_var_base.strip() + " #number"

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
        df[new_var] = df[new_var].where(df[new_var].notna(), "")
        st.success(f"✅ New column '{new_var}' added.")
        st.dataframe(df[[col1, col2, new_var]].head())
    except Exception as e:
        st.error(f"❌ Error computing new variable: {e}")

# -----------------------------
# Upload to SuAVE
# -----------------------------
st.markdown("---")
st.subheader("📤 Publish Back to SuAVE")

# Help box for cookie retrieval
with st.expander("ℹ️ Help: How to Get Your Session Cookie"):
    st.markdown("""
1. Open [https://suave-net.sdsc.edu](https://suave-net.sdsc.edu) in the **same browser** where you're using this app.
2. Log in to your SuAVE account (if not already logged in).
3. Open Developer Tools (press `F12` or right-click → Inspect).
4. Go to the **Application** tab → **Cookies** → `https://suave-net.sdsc.edu`.
5. Find the cookie named **`connect.sid`**.
6. **Copy its decoded value** (not the URL-encoded string).
7. Paste it below.
""")

cookie_input = st.text_input("🍪 Paste your decoded `connect.sid` cookie here:")

base_name = csv_filename.replace(".csv", "").split("_", 1)[-1]
suggested_name = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
survey_name = st.text_input("📛 Name for New Survey:", value=suggested_name)

if st.button("📦 Upload to SuAVE"):
    if not cookie_input or not survey_name:
        st.warning("⚠️ Please fill in both cookie and survey name before uploading.")
    else:
        try:
            referer = survey_url.split("/main")[0] + "/"
            upload_url = referer + "uploadCSV"

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            session = requests.Session()
            session.cookies.set("connect.sid", cookie_input.strip(), domain="suave-net.sdsc.edu")

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

            upload_response = session.post(upload_url, files=files, data=data, headers=headers)

            if upload_response.status_code == 200:
                new_url = f"{referer}main/file={user}_{survey_name}.csv"
                st.success("✅ Survey uploaded successfully!")
                st.markdown(f"🔗 [Open New Survey in SuAVE]({new_url})")
            else:
                st.error(f"❌ Upload failed ({upload_response.status_code} — {upload_response.reason}). Please ensure you're logged in.")
                st.markdown(f"🔍 Server Response:\n\n```\n{upload_response.text}\n```")
        except Exception as e:
            st.error(f"❌ Failed to upload: {e}")

# -----------------------------
# Return to Home button
# -----------------------------
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
