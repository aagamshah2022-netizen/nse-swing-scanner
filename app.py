import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(
page_title="NSE Swing Scanner",
page_icon="📈"
)

st.title("📈 NSE Swing Scanner")
st.write("Scanner starting...")

symbols = [
"RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
"ITC", "LT", "AXISBANK", "KOTAKBANK", "BAJFINANCE", "MARUTI",
"SUNPHARMA", "TITAN", "TRENT", "TATAMOTORS", "TATASTEEL",
"NTPC", "POWERGRID", "ONGC", "COALINDIA", "ADANIENT",
"ADANIPORTS", "BEL", "HAL", "BHEL", "IRFC", "RVNL", "IREDA",
"SUZLON", "ETERNAL", "PAYTM", "JIOFIN", "DLF", "HINDALCO",
"VEDL", "SAIL", "JSWSTEEL", "JSWENERGY", "TATAPOWER", "GAIL",
"IOC", "BPCL", "CIPLA", "DRREDDY", "DIVISLAB", "LUPIN", "AUBANK",
"FEDERALBNK", "PNB", "BANKBARODA", "CANBK", "IDFCFIRSTB",
"INDUSINDBK", "M&M", "EICHERMOT", "TVSMOTOR", "HEROMOTOCO",
"ASHOKLEY", "APOLLOTYRE", "BOSCHLTD", "MOTHERSON", "BHARATFORG",
"CUMMINSIND", "SIEMENS", "ABB", "CGPOWER", "POLYCAB", "KEI",
"DIXON", "VOLTAS", "HAVELLS", "VGUARD", "ASTRAL", "PIDILITIND",
"ASIANPAINT", "BERGEPAINT", "BRITANNIA", "NESTLEIND", "MARICO",
"DABUR", "GODREJCP", "COLPAL", "HINDUNILVR", "ZENSARTECH",
"COFORGE", "PERSISTENT", "MPHASIS", "LTIM", "TECHM", "HCLTECH",
"WIPRO"
]

results = []

for symbol in symbols:

```
try:
    d = yf.download(
        symbol + ".NS",
        period="400d",
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False
    )

    d = d.dropna(subset=["Open", "High", "Low", "Close"])

    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)

    d = d.dropna(subset=["Open", "High", "Low", "Close"])

    if len(d) < 10:
        continue

    swing = None

    # Find latest confirmed swing low
    for i in range(len(d) - 2, 0, -1):

        if (
            float(d.iloc[i].Low) < float(d.iloc[i - 1].Low)
            and
            float(d.iloc[i].Low) < float(d.iloc[i + 1].Low)
        ):
            swing = i
            break

    if swing is None:
        continue

    low = float(d.iloc[swing].Low)
    target = low * 1.20

    reached = False
    reds = 0
    first = None

    # Check candles after swing low
    for i in range(swing + 1, len(d)):

        o = float(d.iloc[i].Open)
        h = float(d.iloc[i].High)
        c = float(d.iloc[i].Close)
        dt = d.index[i]

        # First find the +20% move
        if not reached:

            if h >= target:
                reached = True
                reds = 0
                first = None
                continue

            # Red candles before +20% are ignored
            continue

        # After +20% move, count red candles
        if c < o:

            if reds == 0:
                first = dt

            reds += 1

            # Two consecutive red candles
            if reds >= 2:

                results.append([
                    symbol,
                    round(low, 2),
                    round(target, 2),
                    dt.strftime("%Y-%m-%d"),
                    round(c, 2)
                ])

                break

        else:
            reds = 0
            first = None

except Exception:
    pass
```

st.subheader("CURRENT MATCHES")

result_df = pd.DataFrame(
results,
columns=[
"Symbol",
"Swing Low",
"+20% Level",
"2nd Red Date",
"Current Close"
]
)

st.dataframe(
result_df,
use_container_width=True
)

st.success(
str(len(results)) + " CURRENT MATCHES"
)
