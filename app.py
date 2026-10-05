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
            return {
                "Symbol": symbol,
                "Status": "NO DATA"
            }

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        required = ["Open", "High", "Low", "Close"]

        if not all(
            col in data.columns
            for col in required
        ):
            return {
                "Symbol": symbol,
                "Status": "MISSING DATA"
            }

        data = data.dropna(
            subset=required
        ).copy()

        if len(data) < 10:
            return {
                "Symbol": symbol,
                "Status": "NOT ENOUGH DATA"
            }

        # =================================================
        # FIND LATEST 3-CANDLE SWING LOW
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

        if latest_swing_index is None:

            return {
                "Symbol": symbol,
                "Status": "NO SWING LOW"
            }

        swing_low = float(
            data.iloc[latest_swing_index]["Low"]
        )

        swing_date = data.index[
            latest_swing_index
        ]

        # =================================================
        # MAX MOVE FROM LATEST SWING LOW
        # =================================================

        future_data = data.iloc[
            latest_swing_index + 1:
        ]

        if future_data.empty:

            return {
                "Symbol": symbol,
                "Swing Low": round(
                    swing_low, 2
                ),
                "Swing Low Date":
                    swing_date.strftime(
                        "%Y-%m-%d"
                    ),
                "Status":
                    "NO DATA AFTER SWING"
            }

        max_high = float(
            future_data["High"].max()
        )

        max_move_percent = (
            (max_high - swing_low)
            / swing_low
        ) * 100

        target = swing_low * 1.20

        # =================================================
        # CHECK +20%
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

            if not reached_20:

                if candle_high >= target:

                    reached_20 = True
                    target_date = candle_date

                continue

            # =================================================
            # AFTER +20% CHECK RED CANDLES
            # =================================================

            if candle_close < candle_open:

                if first_red_date is None:

                    first_red_date = candle_date

                else:

                    second_red_index = i

                    last_five_start = max(
                        0,
                        len(data) - 5
                    )

                    days_old = (
                        len(data) - 1
                    ) - second_red_index

                    if days_old <= 4:

                        return {
                            "Symbol": symbol,
                            "Swing Low":
                                round(
                                    swing_low,
                                    2
                                ),
                            "Swing Low Date":
                                swing_date.strftime(
                                    "%Y-%m-%d"
                                ),
                            "Max Move %":
                                round(
                                    max_move_percent,
                                    2
                                ),
                            "+20% Level":
                                round(
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
                            "Status":
                                "MATCH"
                        }

                    first_red_date = None

            else:

                first_red_date = None

        # =================================================
        # DIAGNOSTIC STATUS
        # =================================================

        if max_move_percent < 20:

            return {
                "Symbol": symbol,
                "Swing Low":
                    round(
                        swing_low,
                        2
                    ),
                "Swing Low Date":
                    swing_date.strftime(
                        "%Y-%m-%d"
                    ),
                "Max Move %":
                    round(
                        max_move_percent,
                        2
                    ),
                "+20% Level":
                    round(
                        target,
                        2
                    ),
                "Status":
                    "NO +20%"
            }

        return {
            "Symbol": symbol,
            "Swing Low":
                round(
                    swing_low,
                    2
                ),
            "Swing Low Date":
                swing_date.strftime(
                    "%Y-%m-%d"
                ),
            "Max Move %":
                round(
                    max_move_percent,
                    2
                ),
            "+20% Level":
                round(
                    target,
                    2
                ),
            "Status":
                "NO 2 RED CANDLES"
        }

    except Exception as e:

        return {
            "Symbol": symbol,
            "Status": "ERROR"
        }


if st.button("SCAN NOW"):

    results = []

    progress = st.progress(0)

    for number, symbol in enumerate(symbols):

        result = scan_stock(symbol)

        results.append(result)

        progress.progress(
            (number + 1) / len(symbols)
        )

    st.success("SCAN COMPLETE")

    result_df = pd.DataFrame(results)

    matches = result_df[
        result_df["Status"] == "MATCH"
    ].copy()

    diagnostics = result_df[
        result_df["Status"] != "MATCH"
    ].copy()

    st.write(
        "Total Stocks:",
        len(symbols)
    )

    st.write(
        "Current Matches:",
        len(matches)
    )

    if not matches.empty:

        st.subheader(
            "CURRENT MATCHES"
        )

        matches = matches.sort_values(
            by="2nd Red Date",
            ascending=False
        )

        st.dataframe(
            matches,
            use_container_width=True
        )

    else:

        st.warning(
            "0 CURRENT MATCHES"
        )

    st.subheader(
        "DIAGNOSTIC"
    )

    st.dataframe(
        diagnostics,
        use_container_width=True
    )
