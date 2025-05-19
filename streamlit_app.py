import streamlit as st
from urllib.parse import urlencode

st.set_page_config(page_title="SUAVE App Launcher", layout="centered")
st.title("🧭 SUAVE Application Launcher")

# --- Read and display query parameters ---
query_params = st.query_params
if query_params:
    st.subheader("🔍 Parsed URL Parameters")
    for k, v in query_params.items():
        st.write(f"**{k}**: {v[0] if isinstance(v, list) else v}")
else:
    st.warning("No URL parameters found. Try launching with `?user=...&csv=...`")

# --- Construct parameter string for URLs ---
param_str = urlencode({k: v[0] if isinstance(v, list) else v for k, v in query_params.items()})

# --- Buttons with navigation ---
st.markdown("---")
st.markdown("### 🎛️ Choose an Application")

col1, col2 = st.columns(2)

with col1:
    st.page_link(
        "pages/1_Arithmetic_Operations.py",
        label="➕ Arithmetic Operations",
        icon="➕",
        use_container_width=True,
        params=query_params,
    )

with col2:
    st.page_link(
        "pages/2_Spatial_Statistics.py",
        label="📊 Spatial Statistics",
        icon="📊",
        use_container_width=True,
        params=query_params,
    )

st.markdown("---")
st.caption("🔁 Query parameters are passed to each app.")
