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

        required = ["Open", "High", "Low", "Close"]

        if not all(col in data.columns for col in required):
            return None

        data = data.dropna(subset=required)

        if len(data) < 10:
            return None

        latest_match = None

        for swing_index in range(1, len(data) - 2):

            current_low = float(data.iloc[swing_index]["Low"])
            previous_low = float(data.iloc[swing_index - 1]["Low"])
            next_low = float(data.iloc[swing_index + 1]["Low"])

            if not (
                current_low < previous_low
                and current_low < next_low
            ):
                continue

            swing_low = current_low
            swing_date = data.index[swing_index]
            target = swing_low * 1.20

            reached = False
            first_red_date = None
            target_date = None

            for i in range(swing_index + 1, len(data)):

                candle_open = float(data.iloc[i]["Open"])
                candle_high = float(data.iloc[i]["High"])
                candle_close = float(data.iloc[i]["Close"])
                candle_date = data.index[i]

                if not reached:

                    if candle_high >= target:
                        reached = True
                        target_date = candle_date

                    continue

                if candle_close < candle_open:

                    if first_red_date is None:

                        first_red_date = candle_date

                    else:

                        latest_match = {
                            "Symbol": symbol,
                            "Swing Low": round(swing_low, 2),
                            "+20% Level": round(target, 2),
                            "Swing Low Date": swing_date.strftime("%Y-%m-%d"),
                            "+20% Date": target_date.strftime("%Y-%m-%d"),
                            "1st Red Date": first_red_date.strftime("%Y-%m-%d"),
                            "2nd Red Date": candle_date.strftime("%Y-%m-%d"),
                            "Current Close": round(candle_close, 2)
                        }

                        break

                else:

                    first_red_date = None

        return latest_match

    except Exception:

        return None


if st.button("SCAN NOW"):

    all_matches = []

    progress = st.progress(0)

    for number, symbol in enumerate(symbols):

        stock_matches = scan_stock(symbol)

        if stock_matches:

            all_matches.extend(stock_matches)

        progress.progress(
            (number + 1) / len(symbols)
        )

    st.success("SCAN COMPLETE")

    st.write("Total Stocks:", len(symbols))
    st.write("Total Matches:", len(all_matches))

    if all_matches:

        result_df = pd.DataFrame(all_matches)

        result_df = result_df.sort_values(
            by="2nd Red Date",
            ascending=False
        )

        st.dataframe(
            result_df,
            use_container_width=True
        )

    else:

        st.warning("0 MATCHES")
