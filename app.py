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
# FIND LATEST MEANINGFUL SWING LOW
# 5 candles LEFT + 5 candles RIGHT
# =========================================================

def find_latest_swing_low(data):

    if len(data) < 11:
        return None

    for i in range(
        len(data) - 6,
        4,
        -1
    ):

        current_low = float(
            data.iloc[i]["Low"]
        )

        left_lows = [
            float(data.iloc[j]["Low"])
            for j in range(i - 5, i)
        ]

        right_lows = [
            float(data.iloc[j]["Low"])
            for j in range(i + 1, i + 6)
        ]

        if (
            current_low < min(left_lows)
            and
            current_low < min(right_lows)
        ):
            return i

    return None


# =========================================================
# SCAN ONE STOCK
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

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):
            data.columns = (
                data.columns
                .get_level_values(0)
            )

        required = [
            "Open",
            "High",
            "Low",
            "Close"
        ]

        if not all(
            col in data.columns
            for col in required
        ):
            return None

        data = data.dropna(
            subset=required
        ).copy()

        if len(data) < 11:
            return None

        # =================================================
        # LATEST MEANINGFUL SWING LOW
        # =================================================

        swing_index = find_latest_swing_low(
            data
        )

        if swing_index is None:
            return None

        swing_low = float(
            data.iloc[swing_index]["Low"]
        )

        swing_date = data.index[
            swing_index
        ]

        # =================================================
        # +20% TARGET
        # =================================================

        target = swing_low * 1.20

        target_reached = False
        target_date = None

        first_red_index = None
        first_red_date = None

        # =================================================
        # START AFTER SWING LOW
        # =================================================

        for i in range(
            swing_index + 1,
            len(data)
        ):

            candle_open = float(
                data.iloc[i]["Open"]
            )

            candle_high = float(
                data.iloc[i]["High"]
            )

            candle_close = float(
                data.iloc[i]["Close"]
            )

            candle_date = data.index[i]

            # =============================================
            # FIRST: WAIT FOR +20%
            # =============================================

            if not target_reached:

                if candle_high >= target:

                    target_reached = True
                    target_date = candle_date

                # +20% candle itself is NOT counted
                # as red candle

                continue

            # =============================================
            # AFTER +20%:
            # FIND 2 CONSECUTIVE RED CANDLES
            # =============================================

            is_red = (
                candle_close < candle_open
            )

            if is_red:

                if first_red_index is None:

                    first_red_index = i
                    first_red_date = candle_date

                else:

                    second_red_index = i

                    # Must be within last 5 trading days
                    last_five_start = max(
                        0,
                        len(data) - 5
                    )

                    if (
                        second_red_index
                        >= last_five_start
                    ):

                        return {
                            "Symbol": symbol,

                            "Swing Low": round(
                                swing_low,
                                2
                            ),

                            "Swing Low Date":
                                swing_date.strftime(
                                    "%Y-%m-%d"
                                ),

                            "+20% Level": round(
                                target,
                                2
                            ),

                            "+20% Date":
                                target_date.strftime(
                                    "%Y-%m-%d"
                                ),

                            "1st Red Date":
                                first_red_date.strftime(
                                    "%Y-%m-%d"
                                ),

                            "2nd Red Date":
                                candle_date.strftime(
                                    "%Y-%m-%d"
                                ),

                            "2nd Red Close": round(
                                candle_close,
                                2
                            )
                        }

                    # If not recent enough,
                    # keep searching for another pair
                    first_red_index = i
                    first_red_date = candle_date

            else:

                # Consecutive condition breaks
                first_red_index = None
                first_red_date = None

        return None

    except Exception:

        return None


# =========================================================
# SCAN BUTTON
# =========================================================

if st.button("SCAN NOW"):

    results = []

    progress = st.progress(0)

    status_text = st.empty()

    total = len(symbols)

    for number, symbol in enumerate(symbols):

        status_text.write(
            f"Scanning {symbol} "
            f"({number + 1}/{total})"
        )

        result = scan_stock(symbol)

        if result is not None:
            results.append(result)

        progress.progress(
            (number + 1) / total
        )

    status_text.empty()

    st.success("SCAN COMPLETE")

    st.write(
        "Total Stocks:",
        total
    )

    st.write(
        "Current Matches:",
        len(results)
    )

    if results:

        result_df = pd.DataFrame(
            results
        )

        result_df = result_df.sort_values(
            by="2nd Red Date",
            ascending=False
        )

        st.dataframe(
            result_df,
            use_container_width=True
        )

    else:

        st.warning(
            "0 CURRENT MATCHES"
        )
