import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="NSE Swing Scanner", page_icon="📈")

st.title("📈 NSE Swing Scanner")
st.caption("CURRENT SCAN — Swing Low → +20% → 2 Consecutive Red Candles")

symbols = [
"RELIANCE",
"TCS",
"INFY",
"HDFCBANK",
"ICICIBANK",
"SBIN",
"BHARTIARTL",
"ITC",
"LT",
"AXISBANK",
"KOTAKBANK",
"BAJFINANCE",
"MARUTI",
"SUNPHARMA",
"TITAN",
"TRENT",
"TATAMOTORS",
"TATASTEEL",
"NTPC",
"POWERGRID",
"ONGC",
"COALINDIA",
"ADANIENT",
"ADANIPORTS",
"BEL",
"HAL",
"BHEL",
"IRFC",
"RVNL",
"IREDA",
"SUZLON",
"ZOMATO",
"ETERNAL",
"PAYTM",
"JIOFIN",
"DLF",
"INDHOTEL",
"HINDALCO",
"VEDL",
"SAIL",
"JSWSTEEL",
"JSWENERGY",
"TATAPOWER",
"GAIL",
"IOC",
"BPCL",
"CIPLA",
"DRREDDY",
"DIVISLAB",
"LUPIN",
"AXISBANK",
"AUBANK",
"FEDERALBNK",
"PNB",
"BANKBARODA",
"CANBK",
"IDFCFIRSTB",
"INDUSINDBK",
"M&M",
"EICHERMOT",
"TVSMOTOR",
"HEROMOTOCO",
"ASHOKLEY",
"APOLLOTYRE",
"BOSCHLTD",
"MOTHERSON",
"BHARATFORG",
"CUMMINSIND",
"SIEMENS",
"ABB",
"CGPOWER",
"POLYCAB",
"KEI",
"DIXON",
"VOLTAS",
"HAVELLS",
"VGUARD",
"ASTRAL",
"PIDILITIND",
"ASIANPAINT",
"BERGEPAINT",
"BRITANNIA",
"NESTLEIND",
"MARICO",
"DABUR",
"GODREJCP",
"COLPAL",
"HINDUNILVR",
"ZENSARTECH",
"COFORGE",
"PERSISTENT",
"MPHASIS",
"LTIM",
"TECHM",
"HCLTECH",
"WIPRO"
]

start_date = datetime.now() - timedelta(days=400)
end_date = datetime.now()

st.write("Latest completed daily candle will be used.")

if st.button("🔍 SCAN CURRENT NSE STOCKS", use_container_width=True, type="primary"):

results = []
progress = st.progress(0)
status = st.empty()

total = len(symbols)

for number, symbol in enumerate(symbols, start=1):

    status.write("Scanning " + symbol + " (" + str(number) + "/" + str(total) + ")")

    try:

        data = yf.download(
            symbol + ".NS",
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if data.empty:
            progress.progress(number / total)
            continue

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        required = ["Open", "High", "Low", "Close"]

        if not all(column in data.columns for column in required):
            progress.progress(number / total)
            continue

        data = data[required].copy()

        for column in required:
            data[column] = pd.to_numeric(data[column], errors="coerce")

        data = data.dropna()
        data = data.sort_index()

        if len(data) < 5:
            progress.progress(number / total)
            continue

        latest_swing = None

        for i in range(len(data) - 2, 0, -1):

            current_low = float(data.iloc[i]["Low"])
            previous_low = float(data.iloc[i - 1]["Low"])
            next_low = float(data.iloc[i + 1]["Low"])

            if current_low < previous_low and current_low < next_low:
                latest_swing = i
                break

        if latest_swing is None:
            progress.progress(number / total)
            continue

        swing_low = float(data.iloc[latest_swing]["Low"])
        swing_date = data.index[latest_swing]
        target = swing_low * 1.20

        reached_20 = False
        target_date = None
        red_count = 0
        first_red_date = None

        rejected = False

        for i in range(latest_swing + 1, len(data)):

            candle_open = float(data.iloc[i]["Open"])
            candle_high = float(data.iloc[i]["High"])
            candle_close = float(data.iloc[i]["Close"])
            candle_date = data.index[i]

            if reached_20 == False:

                if candle_high >= target:

                    reached_20 = True
                    target_date = candle_date
                    red_count = 0
                    first_red_date = None
                    continue

                if candle_close < candle_open:

                    red_count = red_count + 1

                    if red_count >= 2:
                        rejected = True
                        break

                else:

                    red_count = 0
                    first_red_date = None

                continue

            if candle_close < candle_open:

                if red_count == 0:
                    first_red_date = candle_date

                red_count = red_count + 1

                if red_count >= 2:

                    results.append(
                        {
                            "Symbol": symbol,
                            "Swing Low": round(swing_low, 2),
                            "Swing Low Date": swing_date.strftime("%Y-%m-%d"),
                            "+20% Level": round(target, 2),
                            "+20% Date": target_date.strftime("%Y-%m-%d"),
                            "1st Red": first_red_date.strftime("%Y-%m-%d"),
                            "2nd Red": candle_date.strftime("%Y-%m-%d"),
                            "Current Close": round(candle_close, 2),
                            "Status": "MATCH"
                        }
                    )

                    break

            else:

                red_count = 0
                first_red_date = None

    except Exception:
        pass

    progress.progress(number / total)

progress.empty()
status.empty()

st.divider()

if len(results) > 0:

    result_df = pd.DataFrame(results)

    st.success(
        str(len(result_df)) + " CURRENT MATCHES FOUND"
    )

    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning("No CURRENT MATCH found.")

else:

st.info("Click the button to scan current NSE stocks.")
