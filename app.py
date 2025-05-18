import streamlit as st

st.set_page_config(page_title="URL Parameter Viewer", layout="centered")
st.title("🔍 SUAVE URL Parameter Viewer")

# ✅ Updated query param access
query_params = st.query_params

if query_params:
    st.subheader("📦 Parsed Parameters")
    for key, value in query_params.items():
        # value is always a list, even if a single item
        display_value = value[0] if len(value) == 1 else value
        st.write(f"**{key}**: {display_value}")
else:
    st.warning("No URL parameters detected. Add parameters like `?user=...&csv=...` to the URL.")

st.markdown("---")

st.markdown("Example:")
example_url = "?user=suavedemos&csv=suavedemos_Picasso_with_Colors.csv&params=none&dzc=https%3A%2F%2Fdzgen.sdsc.edu%2Fdzgen%2Flib-staging-uploads%2Fc460b12f7b6095533062e329f9701bb3%2Fcontent.dzc&activeobject=null&surveyurl=https%3A%2F%2Fsuave-net.sdsc.edu%2Fmain%2Ffile%3Dsuavedemos_Picasso_with_Colors.csv&views=grid%2Cbucket%2Ccrosstab%2Cmap%2Ctable%2Clist%2Cjupyter&view=grid"
st.code(example_url, language="bash")
