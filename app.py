import streamlit as st
import yfinance as yf

st.set_page_config(page_title="NSE Swing Scanner")

st.title("NSE Swing Scanner")

st.write("Testing NSE market data connection...")

data = yf.download(
"RELIANCE.NS",
period="10d",
interval="1d",
progress=False
)

if data.empty:
st.error("NSE DATA NOT RECEIVED")
else:
st.success("NSE DATA CONNECTION WORKING")
st.dataframe(data, use_container_width=True)
