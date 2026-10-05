import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="NSE Swing Scanner Debug", page_icon="🔍")

st.title("NSE Swing Scanner - DEBUG")

symbols = [
"RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
"ITC", "LT", "AXISBANK", "KOTAKBANK", "BAJFINANCE", "MARUTI",
"SUNPHARMA", "TITAN", "TRENT", "TATAMOTORS", "TATASTEEL",
"NTPC", "POWERGRID", "ONGC", "COALINDIA", "ADANIENT",
"ADANIPORTS", "BEL", "HAL", "BHEL", "IRFC", "RVNL", "IREDA",
"SUZLON", "ETERNAL", "PAYTM", "JIOFIN", "DLF", "HINDALCO",
"VEDL", "SAIL", "JSWSTEEL", "JSWENERGY", "TATAPOWER", "GAIL",
"IOC", "BPCL", "CIPLA", "DRREDDY", "DIVISLAB", "LUPIN",
"AUBANK", "FEDERALBNK", "PNB", "BANKBARODA", "CANBK",
"IDFCFIRSTB", "INDUSINDBK", "M&M", "EICHERMOT", "TVSMOTOR",
"HEROMOTOCO", "ASHOKLEY", "APOLLOTYRE", "BOSCHLTD", "MOTHERSON",
"BHARATFORG", "CUMMINSIND", "SIEMENS", "ABB", "CGPOWER", "POLYCAB",
"KEI", "DIXON", "VOLTAS", "HAVELLS", "VGUARD", "ASTRAL",
"PIDILITIND", "ASIANPAINT", "BERGEPAINT", "BRITANNIA", "NESTLEIND",
"MARICO", "DABUR", "GODREJCP", "COLPAL", "HINDUNILVR", "ZENSARTECH",
"COFORGE", "PERSISTENT", "MPHASIS", "LTIM", "TECHM", "HCLTECH",
"WIPRO"
]

results = []
debug_rows = []

total = len(symbols)
data_ok = 0
swing_found = 0
plus20_reached = 0
one_red_found = 0
two_red_found = 0
errors = 0

for symbol in symbols:
    try:
d = yf.download(
symbol + ".NS",
period="400d",
interval="1d",
auto_adjust=False,
progress=False,
threads=False
)

```
    if d.empty:
        debug_rows.append([symbol, "NO DATA", "", "", "", "", ""])
        continue

    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close"]

    if not all(col in d.columns for col in required):
        debug_rows.append([symbol, "MISSING COLUMNS", "", "", "", "", ""])
        continue

    d = d.dropna(subset=required)

    if len(d) < 10:
        debug_rows.append([
            symbol, "NOT ENOUGH DATA", len(d), "", "", "", ""
        ])
        continue

    data_ok += 1

    swing = None

    for i in range(len(d) - 2, 0, -1):
        current_low = float(d.iloc[i]["Low"])
        previous_low = float(d.iloc[i - 1]["Low"])
        next_low = float(d.iloc[i + 1]["Low"])

        if current_low < previous_low and current_low < next_low:
            swing = i
            break

    if swing is None:
        debug_rows.append([
            symbol, "NO SWING LOW", len(d), "", "", "", ""
        ])
        continue

    swing_found += 1

    swing_date = d.index[swing]
    swing_low = float(d.iloc[swing]["Low"])
    target = swing_low * 1.20

    reached = False
    reds = 0
    first_red_date = None
    target_date = None

    for i in range(swing + 1, len(d)):
        o = float(d.iloc[i]["Open"])
        h = float(d.iloc[i]["High"])
        c = float(d.iloc[i]["Close"])
        dt = d.index[i]

        if not reached:
            if h >= target:
                reached = True
                target_date = dt
                plus20_reached += 1
            continue

        if c < o:
            if reds == 0:
                first_red_date = dt

            reds += 1

            if reds == 1:
                one_red_found += 1

            if reds >= 2:
                two_red_found += 1

                results.append([
                    symbol,
                    round(swing_low, 2),
                    round(target, 2),
                    swing_date.strftime("%Y-%m-%d"),
                    target_date.strftime("%Y-%m-%d"),
                    first_red_date.strftime("%Y-%m-%d"),
                    dt.strftime("%Y-%m-%d"),
                    round(c, 2)
                ])

                debug_rows.append([
                    symbol,
                    "MATCH",
                    len(d),
                    swing_date.strftime("%Y-%m-%d"),
                    round(swing_low, 2),
                    target_date.strftime("%Y-%m-%d"),
                    dt.strftime("%Y-%m-%d")
                ])

                break
        else:
            reds = 0
            first_red_date = None

    else:
        if not reached:
            debug_rows.append([
                symbol,
                "NO +20% MOVE",
                len(d),
                swing_date.strftime("%Y-%m-%d"),
                round(swing_low, 2),
                round(target, 2),
                ""
            ])

        elif reds == 1:
            debug_rows.append([
                symbol,
                "ONLY 1 RED",
                len(d),
                swing_date.strftime("%Y-%m-%d"),
                round(swing_low, 2),
                round(target, 2),
                ""
            ])

        else:
            debug_rows.append([
                symbol,
                "NO 2 CONSECUTIVE RED",
                len(d),
                swing_date.strftime("%Y-%m-%d"),
                round(swing_low, 2),
                round(target, 2),
                ""
            ])

except Exception as e:
    errors += 1

    debug_rows.append([
        symbol,
        "ERROR",
        "",
        "",
        "",
        "",
        str(e)
    ])
```

st.subheader("DEBUG SUMMARY")

col1, col2, col3 = st.columns(3)

with col1:
st.metric("Total Stocks", total)
st.metric("Data OK", data_ok)
st.metric("Swing Low Found", swing_found)

with col2:
st.metric("+20% Reached", plus20_reached)
st.metric("At Least 1 Red", one_red_found)
st.metric("2 Red Candles", two_red_found)

with col3:
st.metric("Errors", errors)
st.metric("FINAL MATCHES", len(results))

st.subheader("CURRENT MATCHES")

if results:
result_df = pd.DataFrame(
results,
columns=[
"Symbol",
"Swing Low",
"+20% Level",
"Swing Low Date",
"+20% Date",
"1st Red Date",
"2nd Red Date",
"Current Close"
]
)

```
st.dataframe(result_df, use_container_width=True)
```

else:
st.warning("0 CURRENT MATCHES")

st.subheader("DETAILED DEBUG")

debug_df = pd.DataFrame(
debug_rows,
columns=[
"Symbol",
"Status",
"Data Rows",
"Swing Low Date",
"Swing Low",
"+20% Date / Target",
"2nd Red Date / Info"
]
)

st.dataframe(debug_df, use_container_width=True)

st.subheader("STATUS BREAKDOWN")

if not debug_df.empty:
status_counts = (
debug_df["Status"]
.value_counts()
.reset_index()
)

```
status_counts.columns = ["Status", "Count"]

st.dataframe(status_counts, use_container_width=True)
```
