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
# MEANINGFUL SWING LOW
# =========================================================

def is_swing_low(data, i):

    if i < 2 or i >= len(data) - 2:
        return False

    low = float(
        data.iloc[i]["Low"]
    )

    left_1 = float(
        data.iloc[i - 1]["Low"]
    )

    left_2 = float(
        data.iloc[i - 2]["Low"]
    )

    right_1 = float(
        data.iloc[i + 1]["Low"]
    )

    right_2 = float(
        data.iloc[i + 2]["Low"]
    )

    return (
        low < left_1
        and
        low < left_2
        and
        low < right_1
        and
        low < right_2
    )


# =========================================================
# GET ALL MEANINGFUL SWING LOWS
# =========================================================

def get_swing_lows(data):

    lows = []

    for i in range(
        2,
        len(data) - 2
    ):

        if is_swing_low(
            data,
            i
        ):
            lows.append(i)

    return lows


# =========================================================
# TEST ONE SWING LOW
# =========================================================

def test_swing_low(
    data,
    swing_index
):

    swing_low = float(
        data.iloc[swing_index]["Low"]
    )

    swing_date = data.index[
        swing_index
    ]

    target = swing_low * 1.20

    reached_20 = False
    target_index = None

    first_red_index = None

    # -----------------------------------------------------
    # START AFTER SWING LOW
    # -----------------------------------------------------

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

        # =================================================
        # BEFORE +20%
        # =================================================

        if not reached_20:

            # ---------------------------------------------
            # +20% reached
            # ---------------------------------------------

            if candle_high >= target:

                reached_20 = True
                target_index = i

                # +20% candle itself is NOT red #1
                first_red_index = None

                continue

            # ---------------------------------------------
            # BEFORE +20%
            # CHECK 2 CONSECUTIVE RED
            # ---------------------------------------------

            is_red = (
                candle_close < candle_open
            )

            if is_red:

                if first_red_index is None:

                    first_red_index = i

                else:

                    # 2 consecutive red candles
                    # BEFORE +20%
                    #
                    # REJECT THIS SWING LOW

                    return {
                        "status": "REJECT",
                        "reason":
                            "2 RED BEFORE +20%"
                    }

            else:

                first_red_index = None

            continue

        # =================================================
        # AFTER +20%
        # =================================================

        is_red = (
            candle_close < candle_open
        )

        if is_red:

            if first_red_index is None:

                first_red_index = i

            else:

                second_red_index = i

                # -----------------------------------------
                # 2ND RED MUST BE IN LAST 5 TRADING DAYS
                # -----------------------------------------

                last_five_start = max(
                    0,
                    len(data) - 5
                )

                if (
                    second_red_index
                    >= last_five_start
                ):

                    return {
                        "status": "MATCH",

                        "Symbol": None,

                        "Swing Low":
                            round(
                                swing_low,
                                2
                            ),

                        "Swing Low Date":
                            swing_date.strftime(
                                "%Y-%m-%d"
                            ),

                        "+20% Level":
                            round(
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

                        "2nd Red Close":
                            round(
                                candle_close,
                                2
                            )
                    }

                # Old 2-red pair
                # Start looking again

                first_red_index = i

        else:

            # Consecutive condition broken
            first_red_index = None

    # -----------------------------------------------------
    # +20% NOT REACHED
    # -----------------------------------------------------

    return {
        "status": "NO_MATCH"
    }


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
        # ALL MEANINGFUL SWING LOWS
        # =================================================

        swing_lows = get_swing_lows(
            data
        )

        if not swing_lows:
            return None

        # =================================================
        # START FROM MOST RECENT SWING LOW
        # =================================================

        swing_lows = sorted(
            swing_lows,
            reverse=True
        )

        # =================================================
        # TRY EACH SWING LOW
        # NEWER REJECTED LOW -> NEXT LOW
        # =================================================

        for swing_index in swing_lows:

            result = test_swing_low(
                data,
                swing_index
            )

            if result is None:
                continue

            # ---------------------------------------------
            # MATCH
            # ---------------------------------------------

            if result["status"] == "MATCH":

                result["Symbol"] = symbol

                return result

            # ---------------------------------------------
            # REJECT
            #
            # Automatically continue to
            # next older swing low
            # ---------------------------------------------

            if result["status"] == "REJECT":

                continue

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
