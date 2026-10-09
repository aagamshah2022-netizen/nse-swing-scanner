import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import io
import time
import re
from aynse import ipo_past_issues

st.set_page_config(
    page_title="NSE Swing Scanner",
    page_icon="🔍",
    layout="wide"
)

st.title("NSE Swing Scanner")
st.caption(
    "Full NSE • NIFTY 500 • IPO | Swing Low → +20% → 2 Red Candles"
)

YF_PERIOD = "60d"
YF_INTERVAL = "1d"
SWING_LOOKBACK = 30
BATCH_SIZE = 80
RECENT_CANDLES = 5

NSE_LIST_URL = (
    "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
)

NIFTY500_URL = (
    "https://nsearchives.nseindia.com/content/indices/"
    "ind_nifty500list.csv"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/"
}


def clean_symbol(symbol):
    symbol = str(symbol).strip().upper()

    if symbol.endswith(".NS"):
        symbol = symbol[:-3]

    symbol = re.sub(r"\s+", "", symbol)

    return symbol


def normalize_dataframe(data, symbol=None):

    try:

        if data is None or data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):

            if symbol is not None:

                symbol = clean_symbol(symbol)
                ticker = symbol + ".NS"

                level0 = [
                    str(x).upper()
                    for x in data.columns.get_level_values(0)
                ]

                level1 = [
                    str(x).upper()
                    for x in data.columns.get_level_values(1)
                ]

                if ticker.upper() in level0:
                    data = data[ticker].copy()

                elif symbol.upper() in level0:
                    data = data[symbol].copy()

                elif ticker.upper() in level1:
                    data = data.xs(
                        ticker,
                        axis=1,
                        level=1
                    ).copy()

                elif symbol.upper() in level1:
                    data = data.xs(
                        symbol,
                        axis=1,
                        level=1
                    ).copy()

                else:
                    data.columns = (
                        data.columns.get_level_values(0)
                    )

            else:
                data.columns = (
                    data.columns.get_level_values(0)
                )

        required = [
            "Open",
            "High",
            "Low",
            "Close"
        ]

        if not all(
            column in data.columns
            for column in required
        ):
            return pd.DataFrame()

        data = data.dropna(
            subset=required
        ).copy()

        data = data.sort_index()

        return data

    except Exception:

        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_nse_symbols():

    try:

        response = requests.get(
            NSE_LIST_URL,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        df = pd.read_csv(
            io.BytesIO(response.content)
        )

        if "SYMBOL" not in df.columns:
            return []

        symbols = []

        for value in df["SYMBOL"]:

            symbol = clean_symbol(value)

            if symbol and symbol != "NAN":
                symbols.append(symbol)

        return list(
            dict.fromkeys(symbols)
        )

    except Exception:

        return []


@st.cache_data(ttl=3600)
def get_nifty500_symbols():

    urls = [
        NIFTY500_URL,
        (
            "https://www.nseindia.com/content/indices/"
            "ind_nifty500list.csv"
        )
    ]

    for url in urls:

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
                url,
                timeout=30
            )

            if response.status_code != 200:
                continue

            if not response.content:
                continue

            df = pd.read_csv(
                io.BytesIO(response.content)
            )

            df.columns = [
                str(column).strip().upper()
                for column in df.columns
            ]

            if "SYMBOL" not in df.columns:
                continue

            symbols = []

            for value in df["SYMBOL"]:

                symbol = clean_symbol(value)

                if symbol and symbol != "NAN":
                    symbols.append(symbol)

            symbols = list(
                dict.fromkeys(symbols)
            )

            if len(symbols) >= 450:
                return symbols

        except Exception:

            continue

    return []


@st.cache_data(ttl=3600)
def get_ipo_symbols():

    try:

        records = ipo_past_issues(
            boards=["mainboard"]
        )

        if not records:
            return []

        start_date = pd.Timestamp("2020-01-01")

        symbols = []

        for item in records:

            if not isinstance(item, dict):
                continue

            symbol = (
                item.get("symbol")
                or item.get("SYMBOL")
            )

            listing_date = (
                item.get("listing_date")
                or item.get("listingDate")
                or item.get("listed_on")
                or item.get("listedOn")
            )

            if not symbol or not listing_date:
                continue

            symbol = clean_symbol(symbol)

            listed_date = pd.to_datetime(
                listing_date,
                errors="coerce",
                utc=True
            )

            if pd.isna(listed_date):
                continue

            listed_date = listed_date.tz_localize(None)

            if listed_date < start_date:
                continue

            symbols.append(symbol)

        symbols = list(
            dict.fromkeys(symbols)
        )

        return sorted(symbols)

    except Exception as e:

        st.error(
            f"IPO data error: {e}"
        )

        return []
        
def find_swing_low(data):

    if data is None or data.empty:
        return None

    start = max(
        1,
        len(data) - SWING_LOOKBACK
    )

    candidates = []

    for i in range(
        start,
        len(data) - 1
    ):

        swing_low = float(
            data.iloc[i]["Low"]
        )

        previous_low = float(
            data.iloc[i - 1]["Low"]
        )

        next_low = float(
            data.iloc[i + 1]["Low"]
        )

        if not (
            swing_low < previous_low
            and swing_low < next_low
        ):
            continue

        target = swing_low * 1.20

        target_index = None

        for j in range(
            i + 1,
            len(data)
        ):

            high_price = float(
                data.iloc[j]["High"]
            )

            if high_price >= target:

                target_index = j
                break

        if target_index is None:
            continue

        broken = False

        for k in range(
            i + 1,
            target_index + 1
        ):

            later_low = float(
                data.iloc[k]["Low"]
            )

            if later_low < swing_low:

                broken = True
                break

        if broken:
            continue

        candidates.append(
            {
                "index": i,
                "target_index": target_index
            }
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x["index"],
        reverse=True
    )

    return candidates[0]["index"]


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

        if target_index is None:

            if high_price >= target:

                target_index = i

                first_red_index = None

                continue

            if is_red:

                if first_red_index is None:

                    first_red_index = i

                else:

                    return None

            else:

                first_red_index = None

            continue

        if is_red:

            if first_red_index is None:

                first_red_index = i

            else:

                second_red_index = i

                recent_start = max(
                    0,
                    len(data) - RECENT_CANDLES
                )

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
                    "2nd Red Close": round(
                        close_price,
                        2
                    )
                }

        else:

            first_red_index = None

    return None


def process_stock(symbol, data):

    try:

        data = normalize_dataframe(
            data,
            symbol
        )

        if data.empty:
            return None

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


def download_batch(symbols):

    tickers = [
        clean_symbol(symbol) + ".NS"
        for symbol in symbols
    ]

    try:

        return yf.download(
            tickers=tickers,
            period=YF_PERIOD,
            interval=YF_INTERVAL,
            auto_adjust=False,
            progress=False,
            threads=True,
            group_by="ticker"
        )

    except Exception:

        return pd.DataFrame()


def get_stock_from_batch(
    batch_data,
    symbol
):

    ticker = (
        clean_symbol(symbol)
        + ".NS"
    )

    try:

        if batch_data is None:
            return None

        if batch_data.empty:
            return None

        if isinstance(
            batch_data.columns,
            pd.MultiIndex
        ):

            level0 = [
                str(x).upper()
                for x in batch_data.columns.get_level_values(0)
            ]

            level1 = [
                str(x).upper()
                for x in batch_data.columns.get_level_values(1)
            ]

            if ticker.upper() in level0:
                return batch_data[ticker].copy()

            if clean_symbol(symbol).upper() in level0:
                return batch_data[
                    clean_symbol(symbol)
                ].copy()

            if ticker.upper() in level1:
                return batch_data.xs(
                    ticker,
                    axis=1,
                    level=1
                ).copy()

            if clean_symbol(symbol).upper() in level1:
                return batch_data.xs(
                    clean_symbol(symbol),
                    axis=1,
                    level=1
                ).copy()

        return batch_data.copy()

    except Exception:

        return None


def run_scanner(
    symbols,
    scanner_name
):

    results = []

    status = st.empty()

    progress = st.progress(0)

    total = len(symbols)

    if total == 0:
        return []

    batches = [
        symbols[i:i + BATCH_SIZE]
        for i in range(
            0,
            total,
            BATCH_SIZE
        )
    ]

    total_batches = len(batches)

    for batch_number, batch in enumerate(
        batches
    ):

        status.write(
            f"{scanner_name}: "
            f"Batch {batch_number + 1}/"
            f"{total_batches}"
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
                results.append(result)

        progress.progress(
            (batch_number + 1)
            / total_batches
        )

        time.sleep(0.3)

    status.empty()
    progress.empty()

    return results


def display_results(
    results,
    total,
    scanner_name
):

    st.success(
        f"{scanner_name} SCAN COMPLETE"
    )

    st.write(
        "Total Stocks:",
        total
    )

    st.write(
        "Current Matches:",
        len(results)
    )

    if not results:

        st.warning(
            "0 CURRENT MATCHES"
        )

        return

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


tab1, tab2, tab3 = st.tabs(
    [
        "FULL NSE",
        "NIFTY 500",
        "IPO"
    ]
)


with tab1:

    st.subheader(
        "Full NSE Equity Scanner"
    )

    if st.button(
        "SCAN FULL NSE",
        type="primary",
        key="full_nse"
    ):

        st.write(
            "Loading NSE stock list..."
        )

        symbols = get_nse_symbols()

        if not symbols:

            st.error(
                "NSE stock list load nahi ho payi."
            )

        else:

            st.info(
                f"Total NSE Stocks: {len(symbols)}"
            )

            results = run_scanner(
                symbols,
                "FULL NSE"
            )

            display_results(
                results,
                len(symbols),
                "FULL NSE"
            )


with tab2:

    st.subheader(
        "NIFTY 500 Scanner"
    )

    if st.button(
        "SCAN NIFTY 500",
        type="primary",
        key="nifty500"
    ):

        st.write(
            "Loading current NIFTY 500 list from NSE..."
        )

        symbols = get_nifty500_symbols()

        if not symbols:

            st.error(
                "NIFTY 500 list NSE se load nahi ho payi."
            )

        else:

            st.info(
                f"NIFTY 500 Stocks: {len(symbols)}"
            )

            results = run_scanner(
                symbols,
                "NIFTY 500"
            )

            display_results(
                results,
                len(symbols),
                "NIFTY 500"
            )


with tab3:

    st.subheader(
        "IPO Scanner"
    )

    st.write(
        "NSE listed IPO stocks scanner"
    )

    if st.button(
        "SCAN IPO",
        type="primary",
        key="ipo"
    ):

        st.write(
            "Loading IPO stock universe..."
        )

        symbols = get_ipo_symbols()

        if not symbols:

            st.error(
                "IPO stock list load nahi ho payi."
            )

        else:

            st.info(
                f"Stocks available: {len(symbols)}"
            )

            results = run_scanner(
                symbols,
                "IPO"
            )

            display_results(
                results,
                len(symbols),
                "IPO"
            )
