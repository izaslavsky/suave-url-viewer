import streamlit as st
st.set_page_config(page_title="Spatial Statistics", layout="wide")  # Must be first

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

# ----------------------------------------
# ✅ Use experimental_get_query_params (REQUIRED for subpages)
# ----------------------------------------
query_params = st.experimental_get_query_params()
user = query_params.get("user", [""])[0]
csv_filename = query_params.get("csv", [""])[0]

# ----------------------------------------
# 📋 Header
# ----------------------------------------
st.title("📊 Spatial Statistics")
st.markdown(f"🧪 **Streamlit version:** `{st.__version__}`")
st.markdown(f"**User:** `{user}`")
st.markdown(f"**CSV File:** `{csv_filename}`")

if not csv_filename:
    st.error("❌ No CSV filename provided. Use `?csv=...` in the URL.")
    st.stop()

# ----------------------------------------
# 📥 Load CSV from SuAVE
# ----------------------------------------
csv_base_url = "https://suave-net.sdsc.edu/surveys/"
csv_url = csv_base_url + csv_filename
st.markdown(f"🔗 Trying URL: `{csv_url}`")

try:
    response = requests.get(csv_url)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))
except Exception as e:
    st.error(f"❌ Could not fetch CSV: {e}")
    st.stop()

# ----------------------------------------
# 📋 Show columns and detect geometry
# ----------------------------------------
st.subheader("📋 Column Check")
df.columns = df.columns.str.strip()  # remove extra spaces
st.write(df.columns.tolist())
st.write(df.dtypes.head())
st.write(df.head(2))

geometry_col = next((col for col in df.columns if "geometry" in col.lower()), None)
if geometry_col is None:
    st.error("❌ No column with name containing 'geometry' found.")
    st.stop()

try:
    gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df[geometry_col]), crs="EPSG:4326")
except Exception as e:
    st.error(f"❌ Failed to convert WKT to geometry: {e}")
    st.stop()

# ----------------------------------------
# 🗺️ Display map using folium
# ----------------------------------------
st.subheader("🗺️ Map of Features")

centroid = gdf.geometry.centroid.unary_union.centroid
center = [centroid.y, centroid.x]

m = folium.Map(location=center, zoom_start=4, tiles="CartoDB positron")
folium.GeoJson(
    gdf,
    tooltip=folium.GeoJsonTooltip(fields=gdf.select_dtypes(include='object').columns[:4].tolist())
).add_to(m)

streamlit_folium.st_folium(m, width=800, height=500)

# ----------------------------------------
# 🔍 Variable selection for GWR
# ----------------------------------------
numeric_cols = gdf.select_dtypes(include='number').columns.tolist()
dependent_var = st.selectbox("📌 Select Dependent Variable", numeric_cols)
independent_vars = st.multiselect("📈 Select Independent Variables", numeric_cols, default=numeric_cols[:2])

# ----------------------------------------
# 🚀 Run GWR
# ----------------------------------------
if st.button("▶️ Run GWR") and dependent_var and independent_vars:
    coords = list(zip(gdf.geometry.x, gdf.geometry.y))
    y = gdf[[dependent_var]].values
    X = gdf[independent_vars].values

    bw = Sel_BW(coords, y, X).search()
    gwr_model = GWR(coords, y, X, bw=bw)
    gwr_results = gwr_model.fit()

    st.success(f"✅ Bandwidth selected: {bw}")
    st.write("R² Score:", gwr_results.R2)

    coeffs_df = pd.DataFrame(gwr_results.params, columns=['Intercept'] + independent_vars)
    st.subheader("📋 Coefficient Summary")
    st.dataframe(coeffs_df)

    # --- Download coefficients
    coeff_csv = io.StringIO()
    coeffs_df.to_csv(coeff_csv, index=False)
    st.download_button("⬇️ Download Coefficients", data=coeff_csv.getvalue(),
                       file_name="gwr_coefficients.csv", mime="text/csv")

    # --- Residuals and predictions
    residuals_df = pd.DataFrame({
        "geometry_id": df.get("geometry_id", df.index),
        "fitted": gwr_results.predy.flatten(),
        "residual": gwr_results.resid_response.flatten()
    })

    res_csv = io.StringIO()
    residuals_df.to_csv(res_csv, index=False)
    st.download_button("⬇️ Download Residuals & Predictions", data=res_csv.getvalue(),
                       file_name="gwr_residuals.csv", mime="text/csv")

# ----------------------------------------
# 🔙 Return to Home
# ----------------------------------------
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
st.markdown(button_css, unsafe_allow_html=True)
st.markdown(f'<a href="/?{param_str}" class="back-button">⬅️ Return to Home</a>', unsafe_allow_html=True)
