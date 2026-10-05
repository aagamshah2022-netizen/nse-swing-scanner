import streamlit as st
import pandas as pd

st.set_page_config(page_title="NSE Swing Scanner")

st.title("NSE Swing Scanner")

st.write("CURRENT SCANNER")

data = pd.DataFrame(
{
"Status": ["READY"],
"Message": ["App is working"]
}
)

st.dataframe(data, use_container_width=True)

st.success("READY")
