import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="NSE Swing Scanner", page_icon="🔍")

st.title("NSE Swing Scanner")

symbols = [
"RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT",
"AXISBANK","KOTAKBANK","BAJFINANCE","MARUTI","SUNPHARMA","TITAN",
"TRENT","TATAMOTORS","TATASTEEL","NTPC","POWERGRID","ONGC","COALINDIA",
"ADANIENT","ADANIPORTS","BEL","HAL","BHEL","IRFC","RVNL","IREDA",
"SUZLON","ETERNAL","PAYTM","JIOFIN","DLF","HINDALCO","VEDL","SAIL",
"JSWSTEEL","JSWENERGY","TATAPOWER","GAIL","IOC","BPCL","CIPLA",
"DRREDDY","DIVISLAB","LUPIN","AUBANK","FEDERALBNK","PNB","BANKBARODA",
"CANBK","IDFCFIRSTB","INDUSINDBK","M&M","EICHERMOT","TVSMOTOR",
"HEROMOTOCO","ASHOKLEY","APOLLOTYRE","BOSCHLTD","MOTHERSON",
"BHARATFORG","CUMMINSIND","SIEMENS","ABB","CGPOWER","POLYCAB","KEI",
"DIXON","VOLTAS","HAVELLS","VGUARD","ASTRAL","PIDILITIND","ASIANPAINT",
"BERGEPAINT","BRITANNIA","NESTLEIND","MARICO","DABUR","GODREJCP",
"COLPAL","HINDUNILVR","ZENSARTECH","COFORGE","PERSISTENT","MPHASIS",
"LTIM","TECHM","HCLTECH","WIPRO"
]

def scan_stock(symbol):
    try:

    data = yf.download(
        symbol + ".NS",
        period="400d",
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False
    )

    if data.empty:
        return None

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.dropna(subset=["Open","High","Low","Close"])

    if len(data) < 10:
        return None

    swing_index = None

    for i in range(len(data)-2,0,-1):

        low = float(data.iloc[i]["Low"])
        previous_low = float(data.iloc[i-1]["Low"])
        next_low = float(data.iloc[i+1]["Low"])

        if low < previous_low and low < next_low:
            swing_index = i
            break

    if swing_index is None:
        return None

    swing_low = float(data.iloc[swing_index]["Low"])
    swing_date = data.index[swing_index]

    target = swing_low * 1.20

    reached = False
    first_red = None

    for i in range(swing_index+1,len(data)):

        candle_high = float(data.iloc[i]["High"])
        candle_open = float(data.iloc[i]["Open"])
        candle_close = float(data.iloc[i]["Close"])

        candle_date = data.index[i]

        if not reached:

            if candle_high >= target:
                reached = True
                continue

        else:

            if candle_close < candle_open:

                if first_red is None:
                    first_red = candle_date

                else:

                    return {
                        "Symbol": symbol,
                        "Swing Low": round(swing_low,2),
                        "+20% Level": round(target,2),
                        "Swing Low Date": swing_date.strftime("%Y-%m-%d"),
                        "+20% Date": data.index[i-1].strftime("%Y-%m-%d"),
                        "1st Red": first_red.strftime("%Y-%m-%d"),
                        "2nd Red": candle_date.strftime("%Y-%m-%d"),
                        "Close": round(candle_close,2)
                    }

            else:
                first_red = None

    return None

except Exception:
    return None

if st.button("SCAN NOW"):

matches = []

progress = st.progress(0)

for number,symbol in enumerate(symbols):

    result = scan_stock(symbol)

    if result is not None:
        matches.append(result)

    progress.progress((number+1)/len(symbols))

st.success("SCAN COMPLETE")

st.write("Total Stocks:",len(symbols))
st.write("Matches:",len(matches))

if len(matches) > 0:

    result_df = pd.DataFrame(matches)

    st.dataframe(
        result_df,
        use_container_width=True
    )

else:

    st.warning("0 MATCHES")
