import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(
    page_title="NSE Swing Scanner",
    page_icon="🔍"
)

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


# =========================================================
# FIND RECENT MEANINGFUL SWING LOW
# =========================================================

def find_recent_swing_low(data):

    # Only recent 30 trading sessions
    start = max(2, len(data) - 30)
    end = len(data) - 2

    for i in range(end, start - 1, -1):

        low = float(data.iloc[i]["Low"])

        left1 = float(data.iloc[i - 1]["Low"])
        left2 = float(data.iloc[i - 2]["Low"])

        right1 = float(data.iloc[i + 1]["Low"])
        right2 = float(data.iloc[i + 2]["Low"])

        if (
            low < left1
            and low < left2
            and low < right1
            and low < right2
        ):
            return i

    return None


# =========================================================
# SCAN STOCK
# =========================================================

def scan_stock(symbol):

    try:

        data = yf.download(
            symbol + ".NS",
            period="60d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if data.empty:
            return None

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna(
            subset=[
                "Open",
                "High",
                "Low",
                "Close"
            ]
        ).copy()

        if len(data) < 15:
            return None

        # -------------------------------------------------
        # LATEST RECENT SWING LOW
        # -------------------------------------------------

        swing_index = find_recent_swing_low(data)

        if swing_index is None:
            return None

        swing_low = float(
            data.iloc[swing_index]["Low"]
        )

        swing_date = data.index[swing_index]

        target = swing_low * 1.20

        target_index = None

        # -------------------------------------------------
        # AFTER SWING LOW
        # -------------------------------------------------

        first_red_index = None

        for i in range(
            swing_index + 1,
            len(data)
        ):

            open_price = float(
                data.iloc[i]["Open"]
            )

            high_price = float(
                data.iloc[i]["High"]
            )

            close_price = float(
                data.iloc[i]["Close"]
            )

            # =================================================
            # TARGET NOT HIT YET
            # =================================================

            if target_index is None:

                if high_price >= target:

                    target_index = i

                    # +20% candle itself is ignored
                    first_red_index = None

                    continue

                # If 2 consecutive red candles happen
                # before +20%, this swing low fails.

                if close_price < open_price:

                    if first_red_index is None:

                        first_red_index = i

                    else:

                        # This swing low is rejected.
                        return None

                else:

                    first_red_index = None

                continue

            # =================================================
            # TARGET ALREADY HIT
            # =================================================

            if close_price < open_price:

                if first_red_index is None:

                    first_red_index = i

                else:

                    second_red_index = i

                    # 2nd red must be within last 5 sessions

                    if second_red_index >= len(data) - 5:

                        return {
                            "Symbol": symbol,
                            "Swing Low": round(
                                swing_low, 2
                            ),
                            "Swing Low Date":
                                swing_date.strftime(
                                    "%Y-%m-%d"
                                ),
                            "+20% Level": round(
                                target, 2
                            ),
                            "+20% Date":
                                data.index[
                                    target_index
                                ].strftime(
                                    "%Y-%m-%d"
                                ),
                            "1st Red Date":
                                data.index[
                                    first_red_index
                                ].strftime(
                                    "%Y-%m-%d"
                                ),
                            "2nd Red Date":
                                data.index[
                                    second_red_index
                                ].strftime(
                                    "%Y-%m-%d"
                                ),
                            "2nd Red Close": round(
                                close_price, 2
                            )
                        }

                    first_red_index = i

            else:

                first_red_index = None

        return None

    except Exception:

        return None


# =========================================================
# RUN SCANNER
# =========================================================

if st.button("SCAN NOW"):

    results = []

    progress = st.progress(0)

    status = st.empty()

    for number, symbol in enumerate(symbols):

        status.write(
            f"Scanning {symbol} "
            f"({number + 1}/{len(symbols)})"
        )

        result = scan_stock(symbol)

        if result is not None:
            results.append(result)

        progress.progress(
            (number + 1) / len(symbols)
        )

    status.empty()

    st.success("SCAN COMPLETE")

    st.write(
        "Total Stocks:",
        len(symbols)
    )

    st.write(
        "Current Matches:",
        len(results)
    )

    if results:

        df = pd.DataFrame(results)

        df = df.sort_values(
            "2nd Red Date",
            ascending=False
        )

        st.dataframe(
            df,
            use_container_width=True
        )

    else:

        st.warning(
            "0 CURRENT MATCHES"
        )
