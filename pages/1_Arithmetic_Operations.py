import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
from urllib.parse import urlencode, urlparse
from datetime import datetime

# ---- Page config ----
st.set_page_config(page_title="Arithmetic Operations", layout="wide")

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

# ---- Define arithmetic operation ----
st.markdown("---")
st.subheader("🧮 Define a New Derived Variable")

numeric_cols = df.select_dtypes(include='number').columns.tolist()
mode = st.radio("Select Operation Type", ["Binary (e.g. A + B)", "Monadic (e.g. log(A))"])

def apply_mono(series, op):
    try:
        if op == "log":
            return np.log(series)
        elif op == "sqrt":
            return np.sqrt(series)
        elif op == "abs":
            return np.abs(series)
        elif op == "square":
            return series ** 2
        elif op == "negate":
            return -series
    except Exception:
        return pd.Series([np.nan] * len(series), index=series.index)
    return series

if mode == "Binary (e.g. A + B)":
    col1 = st.selectbox("➕ First Operand", numeric_cols, key="bin_col1")
    mono1 = st.selectbox("🔁 Apply to First Operand", ["(none)", "log", "sqrt", "abs", "square", "negate"], key="mono1")
    operation = st.selectbox("⚙️ Operation", ["+", "-", "*", "/"], key="bin_op")
    col2 = st.selectbox("➕ Second Operand", numeric_cols, key="bin_col2")
    mono2 = st.selectbox("🔁 Apply to Second Operand", ["(none)", "log", "sqrt", "abs", "square", "negate"], key="mono2")
else:
    monadic_op = st.selectbox("🔁 Unary Operation", ["log", "sqrt", "abs", "square", "negate"], key="mon_op")
    col1 = st.selectbox("🔘 Column to Transform", numeric_cols, key="mono_col")

new_var_base = st.text_input("📝 Name for the New Variable", value="new_var")
new_var = new_var_base.strip() + " #number"
round_digits = st.slider("🔢 Decimal places to round", 0, 6, 2)

if st.button("▶️ Compute"):
    try:
        if mode.startswith("Binary"):
            s1 = apply_mono(df[col1], mono1) if mono1 != "(none)" else df[col1]
            s2 = apply_mono(df[col2], mono2) if mono2 != "(none)" else df[col2]

            if operation == "+":
                df[new_var] = s1 + s2
            elif operation == "-":
                df[new_var] = s1 - s2
            elif operation == "*":
                df[new_var] = s1 * s2
            elif operation == "/":
                df[new_var] = s1 / s2
        else:
            s1 = apply_mono(df[col1], monadic_op)
            df[new_var] = s1

        df[new_var] = df[new_var].round(round_digits).where(df[new_var].notna(), '')

        st.session_state.modified_df = df.copy()
        st.session_state.last_new_var = new_var

        st.success(f"✅ New column '{new_var}' added.")
        st.dataframe(df[[col1, new_var]].head())
    except Exception as e:
        st.error(f"❌ Error computing new variable: {e}")

# ---- Upload to SuAVE ----
st.markdown("---")
st.subheader("📤 Publish Back to SuAVE")

from suave_uploader import upload_to_suave

auth_user = st.text_input("🔐 SuAVE Login:")
auth_password = st.text_input("🔑 SuAVE Password:", type="password")

base_name = csv_filename.replace(".csv", "").split("_", 1)[-1]
suggested_name = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
survey_name = st.text_input("📛 Name for New Survey:", value=suggested_name)

if st.button("📦 Upload to SuAVE"):
    if not survey_name or not auth_user or not auth_password:
        st.warning("⚠️ Please fill in all fields before uploading.")
    else:
        df_to_upload = st.session_state.get("modified_df", df)

        if "last_new_var" in st.session_state:
            st.info(f"🔄 The variable **{st.session_state.last_new_var}** will be included in the uploaded survey.")

        parsed = urlparse(survey_url)
        referer = survey_url.split("/main")[0] + "/"

        success, message, new_url = upload_to_suave(
            df_to_upload,
            survey_name,
            auth_user,
            auth_password,
            referer,
            dzc_file=dzc_file
        )

        if success:
            st.success(message)
            st.markdown(f"🔗 [Open New Survey in SuAVE]({new_url})")
        else:
            st.error(f"❌ {message}")


# ---- Return to Home button ----
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
