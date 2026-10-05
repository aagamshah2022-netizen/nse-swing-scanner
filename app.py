import streamlit as st

st.set_page_config(
    page_title="NSE Swing Scanner",
    page_icon="📈",
    layout="wide"
)

st.title("📈 NSE Swing Scanner")

st.markdown("""
### Scanner Rules

1. 3-candle Swing Low
2. Swing Low se minimum +20% High
3. +20% wali candle red count mein nahi aayegi
4. +20% se pehle 2 consecutive red candles = Reject
5. +20% ke baad 2 consecutive red candles = Match
6. Green candle aane par red count reset
7. +20% ki koi upper limit nahi
8. Match ke baad hi fresh Swing Low scan
9. Active setup ke dauran new Swing Low scan nahi
10. Listing date se pehle ka data ignore
""")

st.success("Scanner App Successfully Running!")

st.info(
    "Next step: NSE historical data connection + exact scanner engine."
)

if st.button("SCAN NSE STOCKS"):
    st.warning("NSE data engine next step mein connect kiya jayega.")
