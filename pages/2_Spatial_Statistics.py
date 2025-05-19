import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from urllib.parse import urlencode
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
import io

# --- Page Setup ---
st.set_page_config(page_title="Spatial Statistics", layout="wide")
st.title("📊 Spatial Statistics")

# --- Extract query parameters ---
query_params = st.query_params
user = query_params.get("user", [None])[0]
csv_url = query_params.get("csv", [None])[0]

if not csv_url:
    st.error("No CSV URL provided. Please pass `?csv=...` in the URL.")
    st.stop()

st.markdown(f"**User:** `{user}`")
st.markdown(f"**CSV File:** `{csv_url}`")

# --- Load CSV ---
try:
    csv_base_url = "https://suave-net.sdsc.edu/surveys/"
    df = pd.read_csv(csv_base_url + csv_url)

except Exception as e:
    st.error(f"Failed to load CSV: {e}")
    st.stop()

st.subheader("📋 Column Check")
st.write(df.columns.tolist())
st.write(df.dtypes)
st.write(df.head(3))


# --- Detect and convert geometry ---
geometry_col = next((col for col in df.columns if "geometry" in col.lower()), None)
if geometry_col is None:
    st.error("No geometry column detected.")
    st.stop()

gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df[geometry_col]), crs="EPSG:4326")

# --- Map Preview ---
st.subheader("🗺️ Map of Features")
st.map(gdf)

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

    # --- Optional: export coefficients ---
    buffer = io.StringIO()
    coeffs_df.to_csv(buffer, index=False)
    st.download_button(
        label="⬇️ Download Coefficients as CSV",
        data=buffer.getvalue(),
        file_name="gwr_coefficients.csv",
        mime="text/csv"
    )

    # Optional: Residuals and predictions
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
