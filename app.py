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

        required = ["Open", "High", "Low", "Close"]

        if not all(col in data.columns for col in required):
            return None

        data = data.dropna(
            subset=required
        ).copy()

        if len(data) < 10:
            return None

        # =================================================
        # FIND LATEST SWING LOW
        # =================================================

        latest_swing_index = None

        for i in range(
            len(data) - 2,
            0,
            -1
        ):

            current_low = float(
                data.iloc[i]["Low"]
            )

            previous_low = float(
                data.iloc[i - 1]["Low"]
            )

            next_low = float(
                data.iloc[i + 1]["Low"]
            )

            if (
                current_low < previous_low
                and
                current_low < next_low
            ):

                latest_swing_index = i
                break

        # No swing low
        if latest_swing_index is None:
            return None

        # =================================================
        # LATEST SWING LOW DETAILS
        # =================================================

        swing_low = float(
            data.iloc[latest_swing_index]["Low"]
        )

        swing_date = data.index[
            latest_swing_index
        ]

        target = swing_low * 1.20

        # =================================================
        # FIND +20% AFTER LATEST SWING LOW
        # =================================================

        reached_20 = False
        target_date = None

        first_red_date = None

        for i in range(
            latest_swing_index + 1,
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

            # ---------------------------------------------
            # FIRST: FIND +20%
            # ---------------------------------------------

            if not reached_20:

                if candle_high >= target:

                    reached_20 = True
                    target_date = candle_date

                continue

            # ---------------------------------------------
            # AFTER +20%: FIND 2 CONSECUTIVE RED CANDLES
            # ---------------------------------------------

            if candle_close < candle_open:

                # First red candle
                if first_red_date is None:

                    first_red_date = candle_date

                # Second consecutive red candle
                else:

                    second_red_index = i

                    # -------------------------------------
                    # 2ND RED MUST BE WITHIN LAST 5
                    # TRADING DAYS
                    # -------------------------------------

                    last_five_start = max(
                        0,
                        len(data) - 5
                    )

                    if second_red_index < last_five_start:
                        return None

                    return {
                        "Symbol": symbol,
                        "Swing Low": round(
                            swing_low, 2
                        ),
                        "+20% Level": round(
                            target, 2
                        ),
                        "Swing Low Date":
                            swing_date.strftime(
                                "%Y-%m-%d"
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
                            candle_close, 2
                        )
                    }

            else:

                # Consecutive red sequence broken
                first_red_date = None

        # =================================================
        # IF LATEST SWING LOW NEVER REACHED +20%
        # =================================================

        return None

    except Exception:

        return None


# =========================================================
# SCAN BUTTON
# =========================================================

if st.button("SCAN NOW"):

    all_matches = []

    progress = st.progress(0)

    for number, symbol in enumerate(symbols):

        stock_match = scan_stock(symbol)

        if stock_match is not None:

            all_matches.append(
                stock_match
            )

        progress.progress(
            (number + 1) / len(symbols)
        )

    st.success("SCAN COMPLETE")

    st.write(
        "Total Stocks:",
        len(symbols)
    )

    st.write(
        "Current Matches:",
        len(all_matches)
    )

    if all_matches:

        result_df = pd.DataFrame(
            all_matches
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
