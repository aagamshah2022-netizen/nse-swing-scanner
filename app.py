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

        data = data.dropna(subset=required).copy()

        if len(data) < 10:
            return None

        # -------------------------------------------------
        # ONLY LAST 5 TRADING DAYS CAN BE THE 2ND RED CANDLE
        # -------------------------------------------------

        recent_start = max(0, len(data) - 5)

        possible_matches = []

        # Check every swing low in available 60-day data
        for swing_index in range(1, len(data) - 2):

            swing_low = float(data.iloc[swing_index]["Low"])

            previous_low = float(
                data.iloc[swing_index - 1]["Low"]
            )

            next_low = float(
                data.iloc[swing_index + 1]["Low"]
            )

            # Swing Low
            if not (
                swing_low < previous_low
                and swing_low < next_low
            ):
                continue

            swing_date = data.index[swing_index]

            # +20% target
            target = swing_low * 1.20

            reached_20 = False
            target_date = None

            first_red_date = None

            # Start checking after swing low
            for i in range(swing_index + 1, len(data)):

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

                # -----------------------------------------
                # STEP 1: FIND +20% MOVE
                # -----------------------------------------

                if not reached_20:

                    if candle_high >= target:

                        reached_20 = True
                        target_date = candle_date

                    continue

                # -----------------------------------------
                # STEP 2: FIND 2 CONSECUTIVE RED CANDLES
                # -----------------------------------------

                if candle_close < candle_open:

                    # First red candle
                    if first_red_date is None:

                        first_red_date = candle_date

                    # Second consecutive red candle
                    else:

                        second_red_position = i

                        # IMPORTANT:
                        # 2nd red must be in LAST 5 TRADING DAYS
                        if second_red_position >= recent_start:

                            possible_matches.append({
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
                            })

                        # This pair is complete.
                        # Continue searching for a newer setup.
                        first_red_date = None

                else:

                    # Consecutive red sequence broken
                    first_red_date = None

        # -------------------------------------------------
        # ONLY THE MOST RECENT CURRENT SETUP
        # -------------------------------------------------

        if not possible_matches:
            return None

        result = sorted(
            possible_matches,
            key=lambda x: x["2nd Red Date"],
            reverse=True
        )[0]

        return result

    except Exception:

        return None


if st.button("SCAN NOW"):

    all_matches = []

    progress = st.progress(0)

    for number, symbol in enumerate(symbols):

        stock_match = scan_stock(symbol)

        if stock_match is not None:
            all_matches.append(stock_match)

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

        st.warning(
            "0 CURRENT MATCHES"
        )
