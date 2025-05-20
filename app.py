import streamlit as st
from urllib.parse import urlencode

st.set_page_config(page_title="SUAVE App Launcher", layout="centered")
st.title("🧭 SUAVE Application Launcher")

# --- Read and display query parameters ---
query_params = st.query_params
if query_params:
    st.markdown("### <small>🔍 Parsed URL Parameters</small>", unsafe_allow_html=True)
    for k, v in query_params.items():
        st.markdown(
            f"<div style='font-size: 0.8em; margin-left: 1em;'>• <b>{k}</b>: {v[0] if isinstance(v, list) else v}</div>",
            unsafe_allow_html=True,
        )
else:
    st.warning("No URL parameters found. Try launching with ?user=...&csv=...")

# --- Construct query string ---
param_str = urlencode({k: v[0] if isinstance(v, list) else v for k, v in query_params.items()})

# --- Custom card style ---
st.markdown("""
<style>
.card-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5em;
    margin-top: 1em;
}
.card {
    background-color: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 1.2em;
    width: 280px;
    box-shadow: 1px 1px 5px rgba(0,0,0,0.1);
}
.card a {
    display: inline-block;
    padding: 0.5em 1em;
    margin-top: 0.6em;
    background-color: #1f77b4;
    color: white;
    font-weight: bold;
    border-radius: 5px;
    text-decoration: none;
}
.card a:hover {
    background-color: #135b91;
}
</style>
""", unsafe_allow_html=True)

# --- Render cards ---
st.markdown("---")
st.markdown("### 🎛️ Choose an Application")

st.markdown(f"""
<div class='card-grid'>
    <div class='card'>
        <div style='font-size: 1.1em;'>➕ Arithmetic Operations</div>
        <div style='font-size: 0.9em; margin-top: 0.5em;'>Computing derived variables and adding them to SuAVE</div>
        <a href="/Arithmetic_Operations?{param_str}">Launch</a>
    </div>
    <div class='card'>
        <div style='font-size: 1.1em;'>📊 Spatial Statistics</div>
        <div style='font-size: 0.9em; margin-top: 0.5em;'>Geographically-Weighted Regression with Residuals and Autocorrelation Measures</div>
        <a href="/Spatial_Statistics?{param_str}">Launch</a>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.caption("🔁 Query parameters will persist across apps.")
