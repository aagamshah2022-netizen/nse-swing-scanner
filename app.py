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
    "LTIM","TECHM","HCLTECH","WIPRO",

    "KANOHAR"
]


# =========================================================
# FIND MEANINGFUL SWING LOW
# =========================================================

def find_swing_low(data):

    # Recent area only
    start = max(0, len(data) - 30)

    candidates = []

    for i in range(start, len(data) - 2):

        swing_low = float(data.iloc[i]["Low"])

        # -------------------------------------------------
        # Find first point where +20% is actually reached
        # -------------------------------------------------

        target = swing_low * 1.20
        target_index = None

        for j in range(i + 1, len(data)):

            future_high = float(data.iloc[j]["High"])

            if future_high >= target:
                target_index = j
                break

        if target_index is None:
            continue

        # -------------------------------------------------
        # Important:
        # Before +20% target, if there is a LOWER low,
        # this candle is not the meaningful swing low.
        #
        # Example:
        # 16 Sep = 700
        # 21 Sep = 763
        #
        # 16 Sep remains the meaningful low because
        # 21 Sep is only a higher low inside the same move.
        # -------------------------------------------------

        lower_low_after = False

        for k in range(i + 1, target_index + 1):

            later_low = float(data.iloc[k]["Low"])

            if later_low < swing_low:
                lower_low_after = True
                break

        if lower_low_after:
            continue

        # -------------------------------------------------
        # Check that this is actually a meaningful low
        # rather than a tiny one-day fluctuation.
        #
        # Price should move sufficiently away from it.
        # -------------------------------------------------

        move = (
            (float(data.iloc[target_index]["High"]) - swing_low)
            / swing_low
        ) * 100

        if move >= 20:

            candidates.append({
                "index": i,
                "target_index": target_index,
                "low": swing_low
            })

    if not candidates:
        return None

    # -----------------------------------------------------
    # If multiple lows belong to the same recent move,
    # choose the LOWEST meaningful swing low.
    #
    # This prevents a later higher-low such as 21 Sep
    # from replacing the original 16 Sep swing low.
    # -----------------------------------------------------

    candidates = sorted(
        candidates,
        key=lambda x: x["low"]
    )

    best = candidates[0]

    return best["index"]


# =========================================================
# CHECK FINAL SETUP
# =========================================================

def check_setup(data, swing_index):

    swing_low = float(
        data.iloc[swing_index]["Low"]
    )

    swing_date = data.index[swing_index]

    target = swing_low * 1.20

    target_index = None
    first_red_index = None

    # -----------------------------------------------------
    # Find first candle which reaches +20%
    # -----------------------------------------------------

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
        # BEFORE +20%
        # =================================================

        if target_index is None:

            if high_price >= target:

                target_index = i

                # +20% candle itself is NOT red #1
                first_red_index = None

                continue

            continue

        # =================================================
        # AFTER +20%
        # =================================================

        is_red = (
            close_price < open_price
        )

        if is_red:

            # First red candle
            if first_red_index is None:

                first_red_index = i

            else:

                # Second consecutive red candle
                second_red_index = i

                # Must be recent
                if second_red_index >= len(data) - 5:

                    return {
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
                                close_price,
                                2
                            )
                    }

                # Current red pair was too old.
                # Start a new sequence from this candle.
                first_red_index = i

        else:

            # Consecutive red sequence broken
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

        # -------------------------------------------------
        # Flatten yfinance MultiIndex
        # -------------------------------------------------

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
            c in data.columns
            for c in required
        ):
            return None

        data = data.dropna(
            subset=required
        ).copy()

        if len(data) < 10:
            return None

        # -------------------------------------------------
        # FIND MEANINGFUL SWING LOW
        # -------------------------------------------------

        swing_index = find_swing_low(
            data
        )

        if swing_index is None:
            return None

        # -------------------------------------------------
        # CHECK +20% + 2 RED SETUP
        # -------------------------------------------------

        result = check_setup(
            data,
            swing_index
        )

        if result is None:
            return None

        result["Symbol"] = symbol

        return result

    except Exception:

        return None


# =========================================================
# RUN SCANNER
# =========================================================

if st.button("SCAN NOW"):

    results = []

    progress = st.progress(0)

    status = st.empty()

    total = len(symbols)

    for number, symbol in enumerate(symbols):

        status.write(
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

    status.empty()

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

        df = pd.DataFrame(
            results
        )

        df = df[
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

        df = df.sort_values(
            by="2nd Red Date",
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
