import streamlit as st
import yfinance as yf

st.set_page_config(page_title="NSE Swing Scanner")

st.title("NSE Swing Scanner")

st.write("Testing NSE data...")

data = yf.download("RELIANCE.NS", period="10d", interval="1d", progress=False)

st.write("Rows received:", len(data))

st.dataframe(data, use_container_width=True)
