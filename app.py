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
# FIND CANDIDATE SWING LOWS
# =========================================================

def find_candidate_lows(data):

    candidates = []

    for i in range(0, len(data) - 1):

        current_low = float(
            data.iloc[i]["Low"]
        )

        # -------------------------------------------------
        # A meaningful low should be followed by recovery.
        # We don't use a fixed 3/5 candle pivot here.
        # -------------------------------------------------

        future_high = float(
            data.iloc[i + 1:]["High"].max()
        )

        move_percent = (
            (future_high - current_low)
            / current_low
        ) * 100

        if move_percent >= 20:

            candidates.append(i)

    return candidates


# =========================================================
# CHECK SETUP FROM A PARTICULAR SWING LOW
# =========================================================

def check_setup(data, swing_index):

    swing_low = float(
        data.iloc[swing_index]["Low"]
    )

    swing_date = data.index[swing_index]

    target = swing_low * 1.20

    target_reached = False
    target_index = None

    first_red_index = None

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

        # -------------------------------------------------
        # WAIT FOR +20%
        # -------------------------------------------------

        if not target_reached:

            if candle_high >= target:

                target_reached = True
                target_index = i

            # +20% candle itself is NEVER counted
            # as one of the two red candles.

            continue

        # -------------------------------------------------
        # AFTER +20%, FIND 2 CONSECUTIVE RED CANDLES
        # -------------------------------------------------

        is_red = (
            candle_close < candle_open
        )

        if is_red:

            if first_red_index is None:

                first_red_index = i

            else:

                second_red_index = i

                # Must be among latest 5 trading candles
                last_five_start = max(
                    0,
                    len(data) - 5
                )

                if (
                    second_red_index
                    >= last_five_start
                ):

                    return {
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
                            candle_close,
                            2
                        )
                    }

                # This pair is too old.
                # Start again from current red candle.
                first_red_index = i

        else:

            # Not consecutive anymore
            first_red_index = None

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

        if len(data) < 10:
            return None

        # =================================================
        # FIND ALL CANDIDATE LOWS
        # =================================================

        candidates = find_candidate_lows(
            data
        )

        if not candidates:
            return None

        # =================================================
        # MOST RECENT CANDIDATE FIRST
        # =================================================

        candidates = sorted(
            candidates,
            reverse=True
        )

        # =================================================
        # TEST MOST RECENT QUALIFYING LOW
        # =================================================

        for swing_index in candidates:

            result = check_setup(
                data,
                swing_index
            )

            if result is not None:

                result["Symbol"] = symbol

                return result

        return None

    except Exception:

        return None


# =========================================================
# SCAN
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

        result = scan_stock(
            symbol
        )

        if result is not None:

            results.append(result)

        progress.progress(
            (number + 1) / total
        )

    status_text.empty()

    st.success(
        "SCAN COMPLETE"
    )

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

        result_df = result_df[
            [
                "Symbol",
                "Swing Low",
                "Swing Low Date",
                "+20% Level",
                "+20% Date",
                "1st Red Date",
                "2nd Red Date",
                "2nd Red Close"
            ]
        ]

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
