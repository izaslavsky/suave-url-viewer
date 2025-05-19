import streamlit as st
from urllib.parse import urlencode

st.set_page_config(page_title="SUAVE App Launcher", layout="centered")
st.title("🧭 SUAVE Application Launcher")

# --- Read and display query parameters ---
query_params = st.query_params  # for Streamlit ≥ 1.30
if query_params:
    st.subheader("🔍 Parsed URL Parameters")
    for k, v in query_params.items():
        st.write(f"**{k}**: {v[0] if isinstance(v, list) else v}")
else:
    st.warning("No URL parameters found. Try launching with ?user=...&csv=...")

# --- Construct query string ---
param_str = urlencode({k: v[0] if isinstance(v, list) else v for k, v in query_params.items()})

# --- App Selection Buttons with parameter-preserving links ---
st.markdown("---")
st.markdown("### 🎛️ Choose an Application")

col1, col2 = st.columns(2)

with col1:
    if st.button("➕ Arithmetic Operations"):
        target_url = f"/Arithmetic_Operations?{param_str}"
        st.markdown(f"<script>window.location.href = '{target_url}'</script>", unsafe_allow_html=True)

with col2:
    if st.button("📊 Spatial Statistics"):
        target_url = f"/Spatial_Statistics?{param_str}"
        st.markdown(f"<script>window.location.href = '{target_url}'</script>", unsafe_allow_html=True)

st.markdown("---")
st.caption("🔁 Query parameters will persist as you move between applications.")
