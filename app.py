import streamlit as st

st.set_page_config(page_title="SUAVE Launcher", layout="centered")
st.title("🧭 SUAVE Application Launcher")

# Parse URL parameters
query_params = st.query_params

st.subheader("🔍 URL Parameters")
if query_params:
    for k, v in query_params.items():
        st.write(f"**{k}**: {v[0] if len(v)==1 else v}")
else:
    st.warning("No parameters found. Try adding ?user=...&csv=... etc. to the URL.")

# Application Launcher
st.markdown("### 🚀 Available Applications")

apps = {
    "Arithmetic Operations": "arithmetic_app",
    "Spatial Statistics": "spatial_stats_app"
}

for app_name, app_path in apps.items():
    launch_url = f"/{app_path}"
    st.markdown(f"- [{app_name}]({launch_url})")

st.markdown("---")
st.caption("Powered by Streamlit")
