import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import io
import time


# =====================================================
# PAGE SETTINGS
# =====================================================

st.set_page_config(
    page_title="NSE Swing Scanner",
    page_icon="🔍",
    layout="wide"
)

st.title("NSE Swing Scanner")
st.caption(
    "Full NSE Equity Universe • Major Swing Low → +20% → 2 Consecutive Red Candles"
)


# =====================================================
# SETTINGS
# =====================================================

NSE_LIST_URL = (
    "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
)

YF_PERIOD = "60d"
YF_INTERVAL = "1d"

SWING_LOOKBACK = 30
BATCH_SIZE = 80


# =====================================================
# GET NSE SYMBOLS
# =====================================================

@st.cache_data(ttl=3600)
def get_nse_symbols():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/154.0.0.0 Safari/537.36"
        ),
        "Accept": "text/csv,application/csv,text/plain,*/*",
        "Referer": "https://www.nseindia.com/"
    }

    try:

        response = requests.get(
            NSE_LIST_URL,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        df = pd.read_csv(
            io.BytesIO(response.content)
        )

        if "SYMBOL" not in df.columns:
            return []

        symbols = (
            df["SYMBOL"]
            .astype(str)
            .str.strip()
            .tolist()
        )

        symbols = [
            s
            for s in symbols
            if s
            and s.upper() != "NAN"
            and " " not in s
        ]

        symbols = list(
            dict.fromkeys(symbols)
        )

        return symbols

    except Exception:

        return []


# =====================================================
# FIND MAJOR SWING LOW
# =====================================================

def find_swing_low(data):

    start = max(
        0,
        len(data) - SWING_LOOKBACK
    )

    candidates = []

    for i in range(
        start,
        len(data) - 2
    ):

        swing_low = float(
            data.iloc[i]["Low"]
        )

        target = swing_low * 1.20

        target_index = None

        # ---------------------------------------------
        # FIND FIRST +20% HIT
        # ---------------------------------------------

        for j in range(
            i + 1,
            len(data)
        ):

            future_high = float(
                data.iloc[j]["High"]
            )

            if future_high >= target:

                target_index = j
                break

        if target_index is None:
            continue

        # ---------------------------------------------
        # AFTER THIS LOW, THERE MUST NOT BE
        # A LOWER LOW BEFORE +20%
        # ---------------------------------------------

        lower_low_after = False

        for k in range(
            i + 1,
            target_index + 1
        ):

            later_low = float(
                data.iloc[k]["Low"]
            )

            if later_low < swing_low:

                lower_low_after = True
                break

        if lower_low_after:
            continue

        move = (
            (
                float(data.iloc[target_index]["High"])
                - swing_low
            )
            / swing_low
        ) * 100

        if move >= 20:

            candidates.append(
                {
                    "index": i,
                    "target_index": target_index,
                    "low": swing_low
                }
            )

    if not candidates:
        return None

    # Lowest valid swing low = major low
    candidates = sorted(
        candidates,
        key=lambda x: x["low"]
    )

    return candidates[0]["index"]


# =====================================================
# CHECK SETUP
# =====================================================

def check_setup(data, swing_index):

    swing_low = float(
        data.iloc[swing_index]["Low"]
    )

    swing_date = data.index[
        swing_index
    ]

    target = swing_low * 1.20

    target_index = None

    first_red_index = None


    # =================================================
    # SCAN FORWARD FROM SWING LOW
    # =================================================

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

        is_red = (
            close_price < open_price
        )


        # =================================================
        # BEFORE +20%
        # =================================================

        if target_index is None:

            # ---------------------------------------------
            # FIRST CHECK +20%
            #
            # The candle which FIRST reaches +20%
            # is NOT counted as red candle.
            # ---------------------------------------------

            if high_price >= target:

                target_index = i

                first_red_index = None

                continue


            # ---------------------------------------------
            # +20% NOT REACHED
            #
            # Check consecutive red candles
            # ---------------------------------------------

            if is_red:

                if first_red_index is None:

                    first_red_index = i

                else:

                    # -------------------------------------
                    # TWO CONSECUTIVE RED CANDLES
                    # BEFORE +20%
                    #
                    # INVALID SETUP
                    # -------------------------------------

                    return None

            else:

                first_red_index = None

            continue


        # =================================================
        # AFTER +20%
        # =================================================

        if is_red:

            # ---------------------------------------------
            # FIRST RED CANDLE
            # ---------------------------------------------

            if first_red_index is None:

                first_red_index = i


            else:

                # -----------------------------------------
                # SECOND CONSECUTIVE RED CANDLE
                # -----------------------------------------

                second_red_index = i


                # -----------------------------------------
                # MUST BE RECENT
                # -----------------------------------------

                if second_red_index >= len(data) - 5:

                    return {

                        "Symbol": "",

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


                # Pair too old.
                # Start a new sequence.
                first_red_index = i


        else:

            # ---------------------------------------------
            # GREEN CANDLE BREAKS RED SEQUENCE
            # ---------------------------------------------

            first_red_index = None


    return None


# =====================================================
# PROCESS ONE STOCK
# =====================================================

def process_stock(
    symbol,
    data
):

    try:

        if data is None or data.empty:
            return None


        # ---------------------------------------------
        # FIX MULTIINDEX DATA
        # ---------------------------------------------

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            try:

                if symbol in data.columns.get_level_values(1):

                    data = data.xs(
                        symbol,
                        axis=1,
                        level=1
                    )

                else:

                    data.columns = (
                        data.columns
                        .get_level_values(0)
                    )

            except Exception:

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


        # ---------------------------------------------
        # FIND MAJOR SWING LOW
        # ---------------------------------------------

        swing_index = find_swing_low(
            data
        )


        if swing_index is None:
            return None


        # ---------------------------------------------
        # CHECK COMPLETE SETUP
        # ---------------------------------------------

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


# =====================================================
# DOWNLOAD BATCH
# =====================================================

def download_batch(symbols):

    tickers = [
        symbol + ".NS"
        for symbol in symbols
    ]

    try:

        data = yf.download(
            tickers=tickers,
            period=YF_PERIOD,
            interval=YF_INTERVAL,
            auto_adjust=False,
            progress=False,
            threads=True,
            group_by="ticker"
        )

        return data

    except Exception:

        return pd.DataFrame()


# =====================================================
# GET SINGLE STOCK FROM BATCH
# =====================================================

def get_stock_from_batch(
    batch_data,
    symbol
):

    ticker = symbol + ".NS"

    try:

        if isinstance(
            batch_data.columns,
            pd.MultiIndex
        ):

            level_zero = (
                batch_data.columns
                .get_level_values(0)
            )

            level_one = (
                batch_data.columns
                .get_level_values(1)
            )


            if ticker in level_zero:

                return batch_data[
                    ticker
                ].copy()


            if symbol in level_zero:

                return batch_data[
                    symbol
                ].copy()


            if ticker in level_one:

                return batch_data.xs(
                    ticker,
                    axis=1,
                    level=1
                ).copy()


            if symbol in level_one:

                return batch_data.xs(
                    symbol,
                    axis=1,
                    level=1
                ).copy()


        return None


    except Exception:

        return None


# =====================================================
# SCAN BUTTON
# =====================================================

if st.button(
    "SCAN FULL NSE",
    type="primary"
):

    status = st.empty()

    status.write(
        "Loading complete NSE equity list..."
    )


    # ---------------------------------------------
    # LOAD NSE LIST
    # ---------------------------------------------

    symbols = get_nse_symbols()


    if not symbols:

        st.error(
            "NSE stock list load nahi ho payi."
        )

        st.stop()


    st.info(
        f"Total NSE stocks found: {len(symbols)}"
    )


    results = []


    progress = st.progress(0)


    total = len(symbols)


    batches = [
        symbols[i:i + BATCH_SIZE]
        for i in range(
            0,
            total,
            BATCH_SIZE
        )
    ]


    total_batches = len(
        batches
    )


    # =================================================
    # PROCESS ALL BATCHES
    # =================================================

    for batch_number, batch in enumerate(
        batches
    ):

        status.write(
            f"Downloading batch "
            f"{batch_number + 1}/"
            f"{total_batches} "
            f"({len(batch)} stocks)"
        )


        batch_data = download_batch(
            batch
        )


        for symbol in batch:

            stock_data = (
                get_stock_from_batch(
                    batch_data,
                    symbol
                )
            )


            result = process_stock(
                symbol,
                stock_data
            )


            if result is not None:

                results.append(
                    result
                )


        progress.progress(
            min(
                1.0,
                (
                    batch_number + 1
                )
                / total_batches
            )
        )


        time.sleep(0.5)


    # =================================================
    # RESULTS
    # =================================================

    status.empty()


    st.success(
        "FULL NSE SCAN COMPLETE"
    )


    st.write(
        "Total NSE Stocks:",
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


        columns = [
            "Symbol",
            "Swing Low",
            "Swing Low Date",
            "+20% Level",
            "+20% Date",
            "1st Red Date",
            "2nd Red Date",
            "2nd Red Close"
        ]


        df = df[columns]


        df = df.sort_values(
            by="2nd Red Date",
            ascending=False
        )


        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


    else:

        st.warning(
            "0 CURRENT MATCHES"
        )
