import streamlit as st
st.set_page_config(page_title="Spatial Statistics", layout="wide")  # MUST BE FIRST

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import requests
import io
from urllib.parse import urlencode
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
import folium
import streamlit_folium

# --- Header ---
st.title("📊 Spatial Statistics")
st.markdown(f"🧪 **Streamlit version:** `{st.__version__}`")

# --- Read Query Parameters ---
try:
    query_params = st.query_params  # For Streamlit ≥ 1.30
except AttributeError:
    query_params = st.experimental_get_query_params()  # Fallback for subpages

user = query_params.get("user", [None])[0]
csv_url = query_params.get("csv", [None])[0]

if not csv_url:
    st.error("No CSV URL provided. Please pass ?csv=... in the URL.")
    st.stop()

st.markdown(f"**User:** `{user}`")
st.markdown(f"**CSV File:** `{csv_url}`")

# --- Load CSV via requests ---
csv_base_url = "https://suave-net.sdsc.edu/surveys/"
csv_full_url = csv_base_url + csv_url
st.markdown(f"🔗 **Trying URL:** `{csv_full_url}`")

try:
    response = requests.get(csv_full_url)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))
except Exception as e:
    st.error(f"❌ Could not fetch CSV: {e}")
    st.stop()

# --- Preview columns and types ---
st.subheader("📋 Column Check")
df.columns = df.columns.str.strip()
st.write(df.columns.tolist())
st.write(df.dtypes)
st.write(df.head(3))

# --- Geometry detection ---
geometry_col = next((col for col in df.columns if "geometry" in col.lower()), None)
if geometry_col is None:
    st.error("No geometry column found (e.g., 'geometry', 'geometry#hidden').")
    st.stop()

try:
    gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df[geometry_col]), crs="EPSG:4326")
except Exception as e:
    st.error(f"Failed to convert geometry: {e}")
    st.stop()

# --- Folium map of polygons ---
st.subheader("🗺️ Map of Features")

# Compute map center
centroid = gdf.geometry.centroid.unary_union.centroid
center = [centroid.y, centroid.x]

# Create interactive map
m = folium.Map(location=center, zoom_start=4, tiles="CartoDB positron")

# Add GeoJSON layer
folium.GeoJson(
    gdf,
    tooltip=folium.GeoJsonTooltip(fields=gdf.select_dtypes(include='object').columns[:4].tolist(), aliases=None),
    name="Polygons"
).add_to(m)

streamlit_folium.st_folium(m, width=800, height=500)

# --- Variable selection ---
numeric_cols = gdf.select_dtypes(include='number').columns.tolist()
dependent_var = st.selectbox("Select Dependent Variable", numeric_cols)
independent_vars = st.multiselect("Select Independent Variables", numeric_cols, default=numeric_cols[:2])

# --- Run GWR ---
if st.button("Run GWR") and dependent_var and independent_vars:
    coords = list(zip(gdf.geometry.x, gdf.geometry.y))
    y = gdf[[dependent_var]].values
    X = gdf[independent_vars].values

    bw = Sel_BW(coords, y, X).search()
    gwr_model = GWR(coords, y, X, bw=bw)
    gwr_results = gwr_model.fit()

    st.success(f"✅ Bandwidth selected: {bw}")
    st.write("R² Score:", gwr_results.R2)

    st.subheader("📋 Coefficient Summary")
    coeffs_df = pd.DataFrame(gwr_results.params, columns=['Intercept'] + independent_vars)
    st.dataframe(coeffs_df)

    # --- Download coefficients ---
    buffer = io.StringIO()
    coeffs_df.to_csv(buffer, index=False)
    st.download_button(
        label="⬇️ Download Coefficients as CSV",
        data=buffer.getvalue(),
        file_name="gwr_coefficients.csv",
        mime="text/csv"
    )

    # --- Download residuals ---
    residuals_df = pd.DataFrame({
        "geometry_id": df.get("geometry_id", df.index),
        "fitted": gwr_results.predy.flatten(),
        "residual": gwr_results.resid_response.flatten()
    })

    res_buffer = io.StringIO()
    residuals_df.to_csv(res_buffer, index=False)
    st.download_button(
        label="⬇️ Download Residuals and Predictions",
        data=res_buffer.getvalue(),
        file_name="gwr_residuals.csv",
        mime="text/csv"
    )

# --- Return to Home ---
param_str = urlencode({k: v[0] if isinstance(v, list) else v for k, v in query_params.items()})
button_css = """
<style>
.back-button {
    display: inline-block;
    padding: 0.6em 1.2em;
    margin-top: 1em;
    font-size: 1.1em;
    font-weight: bold;
    color: white;
    background-color: #1f77b4;
    border: none;
    border-radius: 8px;
    text-decoration: none;
}
.back-button:hover {
    background-color: #16699b;
}
</style>
"""
st.markdown("---")
st.markdown(button_css, unsafe_allow_html=True)
st.markdown(
    f'<a href="/?{param_str}" class="back-button">⬅️ Return to Home</a>',
    unsafe_allow_html=True,
)
