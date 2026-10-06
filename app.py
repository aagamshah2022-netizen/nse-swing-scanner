import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import io
import time


st.set_page_config(
    page_title="NSE Swing Scanner",
    page_icon="🔍",
    layout="wide"
)

st.title("NSE Swing Scanner")
st.caption(
    "FULL NSE • NIFTY 500 • IPO | Major Swing Low → +20% → 2 Consecutive Red Candles"
)


# =========================================================
# SETTINGS
# =========================================================

NSE_LIST_URL = (
    "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
)

NIFTY500_URL = (
    "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
)

YF_PERIOD = "60d"
YF_INTERVAL = "1d"

SWING_LOOKBACK = 30
BATCH_SIZE = 80
RECENT_CANDLES = 5

IPO_START_DATE = pd.Timestamp("2025-01-01")


# =========================================================
# COMMON HEADERS
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8"
    ),
    "Referer": "https://www.nseindia.com/"
}


# =========================================================
# NSE EQUITY LIST
# =========================================================

@st.cache_data(ttl=3600)
def get_nse_equity_list():

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        session.get(
            "https://www.nseindia.com/",
            timeout=20
        )

        response = session.get(
            NSE_LIST_URL,
            timeout=30
        )

        response.raise_for_status()

        df = pd.read_csv(
            io.BytesIO(
                response.content
            )
        )

        df.columns = [
            str(c).strip().upper()
            for c in df.columns
        ]

        return df

    except Exception:

        return pd.DataFrame()


# =========================================================
# FULL NSE SYMBOLS
# =========================================================

@st.cache_data(ttl=3600)
def get_nse_symbols():

    df = get_nse_equity_list()

    if df.empty:
        return []

    if "SYMBOL" not in df.columns:
        return []

    symbols = (
        df["SYMBOL"]
        .astype(str)
        .str.strip()
        .tolist()
    )

    symbols = [
        s for s in symbols
        if s
        and s.upper() != "NAN"
        and " " not in s
    ]

    return list(
        dict.fromkeys(symbols)
    )


# =========================================================
# NIFTY 500 - LIVE NSE
# =========================================================

@st.cache_data(ttl=3600)
def get_nifty500_data():

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        session.get(
            "https://www.nseindia.com/",
            timeout=20
        )

        response = session.get(
            NIFTY500_URL,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        records = data.get(
            "data",
            []
        )

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(
            records
        )

        return df

    except Exception:

        return pd.DataFrame()


# =========================================================
# NIFTY 500 SYMBOLS
# =========================================================

@st.cache_data(ttl=3600)
def get_nifty500_symbols():

    df = get_nifty500_data()

    if df.empty:
        return []

    symbol_column = None

    for col in [
        "symbol",
        "SYMBOL"
    ]:

        if col in df.columns:

            symbol_column = col
            break

    if symbol_column is None:
        return []

    symbols = (
        df[symbol_column]
        .astype(str)
        .str.strip()
        .tolist()
    )

    symbols = [
        s for s in symbols
        if s
        and s.upper() != "NAN"
        and " " not in s
    ]

    symbols = list(
        dict.fromkeys(symbols)
    )

    return symbols


# =========================================================
# IPO LIST
# =========================================================

@st.cache_data(ttl=3600)
def get_ipo_list():

    df = get_nse_equity_list()

    if df.empty:
        return pd.DataFrame()

    if "SYMBOL" not in df.columns:
        return pd.DataFrame()

    listing_col = None

    possible_columns = [
        "DATE OF LISTING",
        "DATE_OF_LISTING",
        "LISTING DATE",
        "LISTING_DATE"
    ]

    for col in possible_columns:

        if col in df.columns:

            listing_col = col
            break

    if listing_col is None:
        return pd.DataFrame()

    df = df.copy()

    df["LISTING_DATE"] = pd.to_datetime(
        df[listing_col],
        errors="coerce",
        dayfirst=True
    )

    df = df[
        df["LISTING_DATE"].notna()
    ].copy()

    df = df[
        df["LISTING_DATE"] >= IPO_START_DATE
    ].copy()

    df["SYMBOL"] = (
        df["SYMBOL"]
        .astype(str)
        .str.strip()
    )

    df = df[
        df["SYMBOL"].ne("")
        & df["SYMBOL"].str.upper().ne("NAN")
        & ~df["SYMBOL"].str.contains(
            " ",
            na=False
        )
    ]

    company_col = None

    for col in [
        "NAME OF COMPANY",
        "COMPANY NAME",
        "NAME_OF_COMPANY"
    ]:

        if col in df.columns:

            company_col = col
            break

    if company_col:

        result = df[
            [
                "SYMBOL",
                company_col,
                "LISTING_DATE"
            ]
        ].copy()

        result.columns = [
            "SYMBOL",
            "COMPANY NAME",
            "LISTING_DATE"
        ]

    else:

        result = df[
            [
                "SYMBOL",
                "LISTING_DATE"
            ]
        ].copy()

        result["COMPANY NAME"] = ""

        result = result[
            [
                "SYMBOL",
                "COMPANY NAME",
                "LISTING_DATE"
            ]
        ]

    result = result.drop_duplicates(
        subset=["SYMBOL"]
    )

    result = result.sort_values(
        "LISTING_DATE",
        ascending=False
    )

    return result.reset_index(
        drop=True
    )


# =========================================================
# FIND MAJOR SWING LOW
# =========================================================

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
                float(
                    data.iloc[target_index]["High"]
                ) - swing_low
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

    candidates = sorted(
        candidates,
        key=lambda x: x["low"]
    )

    return candidates[0]["index"]


# =========================================================
# CHECK SETUP
# =========================================================

def check_setup(
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

    target_index = None
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

        is_red = (
            close_price < open_price
        )

        # =============================================
        # BEFORE +20%
        # =============================================

        if target_index is None:

            if high_price >= target:

                target_index = i

                # +20% candle does not count as red
                first_red_index = None

                continue

            if is_red:

                if first_red_index is None:

                    first_red_index = i

                else:

                    # 2 consecutive reds
                    # before +20% = reject
                    return None

            else:

                first_red_index = None

            continue

        # =============================================
        # AFTER +20%
        # =============================================

        if is_red:

            if first_red_index is None:

                first_red_index = i

                continue

            second_red_index = i

            recent_start = max(
                0,
                len(data) - RECENT_CANDLES
            )

            # Old setup is expired
            if second_red_index < recent_start:

                return None

            return {
                "Symbol": "",
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
                "2nd Red Close":
                    round(
                        close_price,
                        2
                    )
            }

        else:

            first_red_index = None

    return None


# =========================================================
# PROCESS STOCK
# =========================================================

def process_stock(
    symbol,
    data
):

    try:

        if data is None or data.empty:
            return None

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            try:

                if symbol in (
                    data
                    .columns
                    .get_level_values(1)
                ):

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

        swing_index = find_swing_low(
            data
        )

        if swing_index is None:
            return None

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
# DOWNLOAD BATCH
# =========================================================

def download_batch(
    symbols
):

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


# =========================================================
# GET ONE STOCK FROM BATCH
# =========================================================

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
                batch_data
                .columns
                .get_level_values(0)
            )

            level_one = (
                batch_data
                .columns
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

        else:

            return batch_data.copy()

        return None

    except Exception:

        return None


# =========================================================
# DISPLAY RESULTS
# =========================================================

def display_results(
    results,
    title,
    total
):

    st.success(
        f"{title} SCAN COMPLETE"
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


# =========================================================
# GENERIC SCAN
# =========================================================

def scan_universe(
    symbols,
    universe_name
):

    if not symbols:

        st.error(
            f"{universe_name} ke stocks nahi mile."
        )

        return

    results = []

    status = st.empty()

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

    for batch_number, batch in enumerate(
        batches
    ):

        status.write(
            f"Downloading "
            f"{universe_name} "
            f"batch "
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
            (
                batch_number + 1
            ) / total_batches
        )

        time.sleep(0.5)

    status.empty()

    progress.empty()

    display_results(
        results,
        universe_name,
        total
    )


# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "📊 FULL NSE",
        "📈 NIFTY 500",
        "🚀 IPO"
    ]
)


# =========================================================
# FULL NSE
# =========================================================

with tab1:

    st.subheader(
        "Full NSE Equity Scanner"
    )

    if st.button(
        "SCAN FULL NSE",
        type="primary",
        key="scan_nse"
    ):

        symbols = get_nse_symbols()

        if not symbols:

            st.error(
                "NSE stock list load nahi ho payi."
            )

            st.stop()

        st.info(
            f"Total NSE Stocks Found: "
            f"{len(symbols)}"
        )

        scan_universe(
            symbols,
            "FULL NSE"
        )


# =========================================================
# NIFTY 500
# =========================================================

with tab2:

    st.subheader(
        "NIFTY 500 Scanner"
    )

    st.caption(
        "Current NIFTY 500 list NSE se automatically fetch hogi."
    )

    if st.button(
        "SCAN NIFTY 500",
        type="primary",
        key="scan_nifty500"
    ):

        symbols = get_nifty500_symbols()

        if not symbols:

            st.error(
                "NIFTY 500 list NSE se load nahi ho payi."
            )

            st.stop()

        st.info(
            f"Current NIFTY 500 Stocks Found: "
            f"{len(symbols)}"
        )

        scan_universe(
            symbols,
            "NIFTY 500"
        )


# =========================================================
# IPO
# =========================================================

with tab3:

    st.subheader(
        "IPO Scanner"
    )

    st.caption(
        "01-Jan-2025 se listed IPOs → Current"
    )

    ipo_df = get_ipo_list()

    if ipo_df.empty:

        st.warning(
            "IPO listing data nahi mil paya."
        )

    else:

        st.info(
            f"IPO Stocks Available: "
            f"{len(ipo_df)}"
        )

        show_ipo_list = st.checkbox(
            "Show IPO List",
            key="show_ipo_list"
        )

        if show_ipo_list:

            display_ipo = ipo_df.copy()

            display_ipo[
                "LISTING_DATE"
            ] = (
                display_ipo[
                    "LISTING_DATE"
                ]
                .dt.strftime(
                    "%Y-%m-%d"
                )
            )

            st.dataframe(
                display_ipo,
                use_container_width=True,
                hide_index=True
            )

        if st.button(
            "SCAN IPO",
            type="primary",
            key="scan_ipo"
        ):

            ipo_symbols = (
                ipo_df["SYMBOL"]
                .astype(str)
                .tolist()
            )

            scan_universe(
                ipo_symbols,
                "IPO"
            )
