import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import libpysal as ps
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
from urllib.parse import urlencode

# Optional: uncomment if running this standalone
# st.set_page_config(page_title="Spatial Statistics", layout="wide")
st.title("📊 Spatial Statistics")

# --- Extract query parameters ---
query_params = st.query_params
user = query_params.get("user", [None])[0]
csv_url = query_params.get("csv", [None])[0]

if not csv_url:
    st.error("No CSV URL provided. Please pass `?csv=...` in the URL.")
    st.stop()

st.markdown(f"**User:** {user}")
st.markdown(f"**CSV File:** `{csv_url}`")

# --- Load data ---
try:
    df = pd.read_csv(f"https://suave-net.sdsc.edu/main/file={csv_url}")
except Exception as e:
    st.error(f"Failed to load CSV: {e}")
    st.stop()

# --- Convert to GeoDataFrame ---
geometry_col = next((col for col in df.columns if "geometry" in col.lower()), None)
if geometry_col is None:
    st.error("No geometry field detected.")
    st.stop()

gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df[geometry_col]))
gdf = gdf.set_crs(epsg=4326)

# --- Map Preview ---
st.subheader("🗺️ Map of Features")
st.map(gdf)

# --- Variable Selection ---
numeric_cols = gdf.select_dtypes(include='number').columns.tolist()
dependent_var = st.selectbox("Select Dependent Variable", numeric_cols)
independent_vars = st.multiselect("Select Independent Variables", numeric_cols, default=numeric_cols[:2])

# --- GWR Analysis ---
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

# --- Navigation back to Home ---
param_str = urlencode({k: v[0] for k, v in st.query_params.items()})
st.markdown("---")
st.markdown(f"[⬅️ Return to Home](../Home?{param_str})", unsafe_allow_html=True)
