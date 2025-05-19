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
    st.warning("No URL parameters found. Try launching with ?user=...&csv=...")

# --- Construct query string ---
param_str = urlencode({k: v[0] if isinstance(v, list) else v for k, v in query_params.items()})

# --- Fake buttons using styled HTML ---
st.markdown("---")
st.markdown("### 🎛️ Choose an Application")

# Define URLs
arith_url = f"/Arithmetic_Operations?{param_str}"
spatial_url = f"/Spatial_Statistics?{param_str}"

# Define custom button styles
button_css = """
<style>
.app-button {
    display: inline-block;
    padding: 0.6em 1.2em;
    margin: 0.4em;
    font-size: 1.1em;
    font-weight: bold;
    color: white;
    background-color: #4CAF50;
    border: none;
    border-radius: 8px;
    text-decoration: none;
    cursor: pointer;
}
.app-button:hover {
    background-color: #45a049;
}
</style>
"""

# Render buttons
st.markdown(button_css, unsafe_allow_html=True)
st.markdown(f'<a class="app-button" href="{arith_url}">➕ Arithmetic Operations</a>', unsafe_allow_html=True)
st.markdown(f'<a class="app-button" href="{spatial_url}">📊 Spatial Statistics</a>', unsafe_allow_html=True)

st.markdown("---")
st.caption("🔁 Query parameters will persist across apps.")
