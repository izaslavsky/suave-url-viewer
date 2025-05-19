import streamlit as st
from urllib.parse import urlencode

st.set_page_config(page_title="SUAVE App Launcher", layout="centered")
st.title("🧭 SUAVE Application Launcher")

query_params = st.query_params

st.subheader("🔍 Parsed URL Parameters")
if query_params:
    for k, v in query_params.items():
        st.write(f"**{k}**: {v[0] if len(v) == 1 else v}")
else:
    st.warning("No parameters found. Add `?user=...&csv=...` to the URL.")

st.markdown("---")

# 🎯 Prepare parameter string for linking
param_str = urlencode({k: v[0] for k, v in query_params.items()}) if query_params else ""

st.markdown("### 🎛️ Choose an Application")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### ➕ Arithmetic Operations")
    st.markdown(
        f"[Go to Arithmetic Operations ➡️](./pages/1_Arithmetic_Operations.py?{param_str})",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown("#### 📊 Spatial Statistics")
    st.markdown(
        f"[Go to Spatial Statistics ➡️](./pages/2_Spatial_Statistics.py?{param_str})",
        unsafe_allow_html=True,
    )

st.markdown("---")
st.caption("Note: Parameters will be preserved when switching between apps.")
