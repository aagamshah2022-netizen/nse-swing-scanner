```python
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
st.caption("Swing Low → +20% Target → 2 Consecutive Red Candles")

YF_PERIOD = "60d"
YF_INTERVAL = "1d"
SWING_LOOKBACK = 30
BATCH_SIZE = 80
RECENT_CANDLES = 5
BACKTEST_START = "2026-01-01"

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
    "Referer": "https://www.nseindia.com/"
}


def clean_symbol(symbol):
    symbol = str(symbol).strip().upper()
    if symbol.endswith(".NS"):
        symbol = symbol[:-3]
    return re.sub(r"\s+", "", symbol)


def normalize_dataframe(data, symbol=None):
    try:
        if data is None or data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
            if symbol:
                ticker = clean_symbol(symbol) + ".NS"
                symbol_clean = clean_symbol(symbol)
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
                elif symbol_clean.upper() in level0:
                    data = data[symbol_clean].copy()
                elif ticker.upper() in level1:
                    data = data.xs(
                        ticker, axis=1, level=1
                    ).copy()
                elif symbol_clean.upper() in level1:
                    data = data.xs(
                        symbol_clean, axis=1, level=1
                    ).copy()
                else:
                    return pd.DataFrame()
            else:
                data.columns = data.columns.get_level_values(0)

        required = ["Open", "High", "Low", "Close"]
        if not all(col in data.columns for col in required):
            return pd.DataFrame()

        data = data.dropna(subset=required).copy()
        data = data.sort_index()
        data = data[~data.index.duplicated(keep="last")]
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
        df = pd.read_csv(io.BytesIO(response.content))

        df.columns = [str(c).strip().upper() for c in df.columns]

        if "SYMBOL" not in df.columns:
            return []

        symbols = [
            clean_symbol(x)
            for x in df["SYMBOL"]
            if clean_symbol(x) not in ("", "NAN")
        ]
        return list(dict.fromkeys(symbols))

    except Exception:
        return []


@st.cache_data(ttl=3600)
def get_nifty500_symbols():
    urls = [
        NIFTY500_URL,
        "https://www.nseindia.com/content/indices/ind_nifty500list.csv"
    ]

    for url in urls:
        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            session.get(
                "https://www.nseindia.com/",
                timeout=20
            )
            response = session.get(url, timeout=30)

            if response.status_code != 200:
                continue

            df = pd.read_csv(io.BytesIO(response.content))
            df.columns = [
                str(col).strip().upper()
                for col in df.columns
            ]

            if "SYMBOL" not in df.columns:
                continue

            symbols = [
                clean_symbol(x)
                for x in df["SYMBOL"]
                if clean_symbol(x) not in ("", "NAN")
            ]
            symbols = list(dict.fromkeys(symbols))

            if len(symbols) >= 450:
                return symbols

        except Exception:
            continue

    return []


def normalize_ipo_records(records):
    """Convert IPO results to a standard list of dictionaries."""
    if isinstance(records, pd.DataFrame):
        return records.to_dict("records")

    if isinstance(records, dict):
        for key in ("data", "records", "results", "issues"):
            if isinstance(records.get(key), list):
                return records[key]
        return [records]

    if isinstance(records, list):
        return records

    return []


def get_ipo_symbol_from_record(item):
    """Read possible symbol and listing-date field names."""
    if not isinstance(item, dict):
        return None, None

    lowered = {
        str(key).strip().lower().replace(" ", "_"): value
        for key, value in item.items()
    }

    symbol = (
        lowered.get("symbol")
        or lowered.get("trading_symbol")
        or lowered.get("ticker")
    )

    listing_date = (
        lowered.get("listing_date")
        or lowered.get("listingdate")
        or lowered.get("listed_on")
        or lowered.get("listedon")
        or lowered.get("date_of_listing")
        or lowered.get("listing_date_time")
    )

    return symbol, listing_date


@st.cache_data(ttl=21600, show_spinner=False)
def get_ipo_symbols():
    """
    Load mainboard IPOs from 2020 onward in yearly chunks.
    A failed year does not prevent other years from loading.
    """
    cutoff = pd.Timestamp("2020-01-01")
    symbols = set()
    successful_years = []
    failed_years = []

    current_year = pd.Timestamp.now(tz="Asia/Kolkata").year

    for year in range(2020, current_year + 1):
        year_records = None
        last_error = None

        # Try each year up to 3 times.
        for attempt in range(3):
            try:
                year_records = ipo_past_issues(
                    f"{year}-01-01",
                    f"{year}-12-31",
                    boards=["mainboard"]
                )
                break
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))

        if year_records is None:
            failed_years.append(year)
            continue

        records = normalize_ipo_records(year_records)
        year_added = 0

        for item in records:
            symbol, listing_date = get_ipo_symbol_from_record(item)

            if not symbol or not listing_date:
                continue

            parsed_date = pd.to_datetime(
                listing_date,
                errors="coerce",
                utc=True
            )

            if pd.isna(parsed_date):
                continue

            try:
                parsed_date = parsed_date.tz_localize(None)
            except (TypeError, AttributeError):
                pass

            if parsed_date < cutoff:
                continue

            cleaned = clean_symbol(symbol)
            if cleaned and cleaned != "NAN":
                symbols.add(cleaned)
                year_added += 1

        successful_years.append(year)

        # Avoid sending requests too quickly to NSE.
        time.sleep(0.25)

    result = sorted(symbols)

    if failed_years:
        st.warning(
            "IPO data kuch saalon ke liye load nahi hua: "
            + ", ".join(map(str, failed_years))
            + ". Retry button se dobara try kar sakte ho."
        )

    if not result:
        st.error(
            "IPO list load nahi hui. NSE data source ya internet "
            "temporarily unavailable ho sakta hai. "
            "IPO list ko dobara load karne ke liye Retry IPO List dabao."
        )

    return result


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


def download_history_batch(symbols, start_date, end_date):
    tickers = [
        clean_symbol(symbol) + ".NS"
        for symbol in symbols
    ]

    try:
        return yf.download(
            tickers=tickers,
            start=start_date,
            end=end_date,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=True,
            group_by="ticker"
        )
    except Exception:
        return pd.DataFrame()


def get_stock_from_batch(batch_data, symbol):
    try:
        if batch_data is None or batch_data.empty:
            return None

        if not isinstance(batch_data.columns, pd.MultiIndex):
            return batch_data.copy()

        ticker = clean_symbol(symbol) + ".NS"
        symbol_clean = clean_symbol(symbol)
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

        if symbol_clean.upper() in level0:
            return batch_data[symbol_clean].copy()

        if ticker.upper() in level1:
            return batch_data.xs(
                ticker, axis=1, level=1
            ).copy()

        if symbol_clean.upper() in level1:
            return batch_data.xs(
                symbol_clean, axis=1, level=1
            ).copy()

        return None

    except Exception:
        return None


def check_setup(data, swing_index, recent_only=False):
    swing_low = float(data.iloc[swing_index]["Low"])
    swing_date = data.index[swing_index]
    target = swing_low * 1.20

    first_red_index = None
    target_index = None

    for i in range(swing_index + 1, len(data)):
        open_price = float(data.iloc[i]["Open"])
        high_price = float(data.iloc[i]["High"])
        close_price = float(data.iloc[i]["Close"])
        low_price = float(data.iloc[i]["Low"])

        if low_price < swing_low:
            return None

        is_red = close_price < open_price

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

                if recent_only:
                    recent_start = max(
                        0, len(data) - RECENT_CANDLES
                    )
                    if second_red_index < recent_start:
                        return None

                return {
                    "Symbol": "",
                    "Swing Low": round(swing_low, 2),
                    "Swing Low Date": pd.Timestamp(
                        swing_date
                    ).strftime("%Y-%m-%d"),
                    "+20% Target": round(target, 2),
                    "Target Hit Date": pd.Timestamp(
                        data.index[target_index]
                    ).strftime("%Y-%m-%d"),
                    "1st Red Date": pd.Timestamp(
                        data.index[first_red_index]
                    ).strftime("%Y-%m-%d"),
                    "2nd Red Date": pd.Timestamp(
                        data.index[second_red_index]
                    ).strftime("%Y-%m-%d"),
                    "2nd Red Close": round(close_price, 2)
                }
        else:
            first_red_index = None

    return None


def process_stock(symbol, data):
    data = normalize_dataframe(data, symbol)

    if data.empty or len(data) < 3:
        return None

    start = max(1, len(data) - SWING_LOOKBACK)

    for i in range(len(data) - 2, start - 1, -1):
        current_low = float(data.iloc[i]["Low"])
        previous_low = float(data.iloc[i - 1]["Low"])
        next_low = float(data.iloc[i + 1]["Low"])

        if current_low < previous_low and current_low < next_low:
            result = check_setup(data, i, recent_only=True)
            if result:
                result["Symbol"] = symbol
                return result

    return None


def run_scanner(symbols, scanner_name):
    results = []
    progress = st.progress(0)
    status = st.empty()

    if not symbols:
        return results

    batches = [
        symbols[i:i + BATCH_SIZE]
        for i in range(0, len(symbols), BATCH_SIZE)
    ]

    for batch_number, batch in enumerate(batches):
        status.write(
            f"{scanner_name}: Batch "
            f"{batch_number + 1}/{len(batches)}"
        )

        batch_data = download_batch(batch)

        for symbol in batch:
            stock_data = get_stock_from_batch(batch_data, symbol)
            result = process_stock(symbol, stock_data)

            if result:
                results.append(result)

        progress.progress(
            (batch_number + 1) / len(batches)
        )
        time.sleep(0.2)

    status.empty()
    progress.empty()
    return results


def run_historical_backtest(symbols, start_date, end_date, scanner_name):
    matches = []

    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)

    history_start = (
        start_ts - pd.Timedelta(days=365)
    ).strftime("%Y-%m-%d")

    history_end = (
        end_ts + pd.Timedelta(days=1)
    ).strftime("%Y-%m-%d")

    batches = [
        symbols[i:i + BATCH_SIZE]
        for i in range(0, len(symbols), BATCH_SIZE)
    ]

    progress = st.progress(0)
    status = st.empty()

    for batch_number, batch in enumerate(batches):
        status.write(
            f"{scanner_name} Backtest: Batch "
            f"{batch_number + 1}/{len(batches)} of {len(batches)}"
        )

        batch_data = download_history_batch(
            batch, history_start, history_end
        )

        for symbol in batch:
            raw = get_stock_from_batch(batch_data, symbol)
            data = normalize_dataframe(raw, symbol)

            if data.empty or len(data) < 3:
                continue

            data = data.sort_index()
            opens = data["Open"].astype(float)
            highs = data["High"].astype(float)
            lows = data["Low"].astype(float)
            closes = data["Close"].astype(float)

            i = 1

            while i < len(data) - 1:
                swing_low = float(lows.iloc[i])

                if not (
                    swing_low < float(lows.iloc[i - 1])
                    and swing_low < float(lows.iloc[i + 1])
                ):
                    i += 1
                    continue

                swing_date = pd.Timestamp(
                    data.index[i]
                ).normalize()
                target = swing_low * 1.20

                target_index = None
                first_red = None
                rejected_before_target = False
                swing_broken = False

                for j in range(i + 1, len(data)):
                    if float(lows.iloc[j]) < swing_low:
                        swing_broken = True
                        break

                    if float(highs.iloc[j]) >= target:
                        target_index = j
                        break

                    is_red = (
                        float(closes.iloc[j]) < float(opens.iloc[j])
                    )

                    if is_red:
                        if first_red is None:
                            first_red = j
                        else:
                            rejected_before_target = True
                            break
                    else:
                        first_red = None

                if swing_broken or rejected_before_target:
                    i += 1
                    continue

                if target_index is None:
                    i += 1
                    continue

                # Target candle itself is excluded from red counting.
                first_red = None
                confirmed = False

                for k in range(target_index + 1, len(data)):
                    is_red = (
                        float(closes.iloc[k]) < float(opens.iloc[k])
                    )

                    if is_red:
                        if first_red is None:
                            first_red = k
                        else:
                            event_date = pd.Timestamp(
                                data.index[k]
                            ).normalize()

                            if start_ts <= event_date <= end_ts:
                                matches.append({
                                    "Scanner": scanner_name,
                                    "Symbol": symbol,
                                    "Swing Low Date": swing_date.strftime("%Y-%m-%d"),
                                    "Swing Low": round(swing_low, 2),
                                    "+20% Target": round(target, 2),
                                    "Target Hit Date": pd.Timestamp(
                                        data.index[target_index]
                                    ).strftime("%Y-%m-%d"),
                                    "1st Red Date": pd.Timestamp(
                                        data.index[first_red]
                                    ).strftime("%Y-%m-%d"),
                                    "2nd Red Date": event_date.strftime("%Y-%m-%d"),
                                    "2nd Red Close": round(
                                        float(closes.iloc[k]), 2
                                    )
                                })

                            i = k + 1
                            confirmed = True
                            break
                    else:
                        first_red = None

                if not confirmed:
                    i += 1

        progress.progress(
            (batch_number + 1) / max(len(batches), 1)
        )
        time.sleep(0.2)

    status.empty()
    progress.empty()

    matches_df = pd.DataFrame(matches)

    if not matches_df.empty:
        matches_df = matches_df.drop_duplicates(
            subset=["Symbol", "Swing Low Date", "2nd Red Date"]
        )
        matches_df = matches_df.sort_values(
            "2nd Red Date", ascending=False
        )

    return matches_df


def display_results(results, total, scanner_name):
    st.success(f"{scanner_name} scan complete")
    st.write(f"Total stocks: {total}")
    st.write(f"Current matches: {len(results)}")

    if not results:
        st.warning("No current matches found.")
        return

    df = pd.DataFrame(results)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Download Current Matches CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{scanner_name.lower().replace(' ', '_')}_current_matches.csv",
        mime="text/csv",
        key=f"current_download_{scanner_name.lower().replace(' ', '_')}"
    )


def show_backtest_section(symbols, scanner_name, key):
    st.subheader(f"{scanner_name} Historical Backtest")
    st.write(
        "Period: 1 January 2026 se latest available daily candle tak."
    )

    if st.button(
        f"RUN {scanner_name} BACKTEST",
        type="primary",
        key=f"backtest_{key}"
    ):
        if not symbols:
            st.error("Stock list load nahi ho payi.")
            return

        start_date = pd.Timestamp("2026-01-01").date()
        end_date = pd.Timestamp.now(
            tz="Asia/Kolkata"
        ).date()

        st.info(
            f"Stocks: {len(symbols)} | "
            f"Period: {start_date} to {end_date}"
        )

        matches_df = run_historical_backtest(
            symbols,
            start_date,
            end_date,
            scanner_name
        )

        st.session_state[f"{key}_matches"] = matches_df

    matches_df = st.session_state.get(
        f"{key}_matches", pd.DataFrame()
    )

    st.subheader(f"Historical Matches: {len(matches_df)}")

    if not matches_df.empty:
        st.dataframe(
            matches_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Matches CSV",
            data=matches_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{key}_backtest_matches_2026.csv",
            mime="text/csv",
            key=f"{key}_matches_csv"
        )
    else:
        st.write(
            "Backtest run karo; matches milne par yahan dikhenge."
        )


tab1, tab2, tab3 = st.tabs(
    ["FULL NSE", "NIFTY 500", "IPO"]
)


with tab1:
    current_tab, history_tab = st.tabs(
        ["Current Scan", "Historical Backtest"]
    )

    with current_tab:
        st.subheader("Full NSE Scanner")

        if st.button(
            "SCAN FULL NSE",
            type="primary",
            key="full_nse"
        ):
            symbols = get_nse_symbols()

            if not symbols:
                st.error("NSE stock list load nahi hui.")
            else:
                st.info(f"Total NSE stocks: {len(symbols)}")
                results = run_scanner(symbols, "FULL NSE")
                display_results(results, len(symbols), "FULL NSE")

    with history_tab:
        symbols = get_nse_symbols()

        if symbols:
            show_backtest_section(
                symbols, "FULL NSE", "full_nse"
            )
        else:
            st.warning("NSE stock list load nahi hui.")


with tab2:
    current_tab, history_tab = st.tabs(
        ["Current Scan", "Historical Backtest"]
    )

    with current_tab:
        st.subheader("NIFTY 500 Scanner")

        if st.button(
            "SCAN NIFTY 500",
            type="primary",
            key="nifty500"
        ):
            symbols = get_nifty500_symbols()

            if not symbols:
                st.error("NIFTY 500 list load nahi hui.")
            else:
                st.info(f"NIFTY 500 stocks: {len(symbols)}")
                results = run_scanner(symbols, "NIFTY 500")
                display_results(results, len(symbols), "NIFTY 500")

    with history_tab:
        symbols = get_nifty500_symbols()

        if symbols:
            show_backtest_section(
                symbols, "NIFTY 500", "nifty500"
            )
        else:
            st.warning("NIFTY 500 list load nahi hui.")


with tab3:
    current_tab, history_tab = st.tabs(
        ["Current Scan", "Historical Backtest"]
    )

    with current_tab:
        st.subheader("IPO Scanner")

        if st.button(
            "RETRY IPO LIST",
            key="retry_ipo_list"
        ):
            get_ipo_symbols.clear()
            st.rerun()

        if st.button(
            "SCAN IPO",
            type="primary",
            key="ipo"
        ):
            get_ipo_symbols.clear()
            symbols = get_ipo_symbols()

            if not symbols:
                st.error(
                    "IPO list abhi load nahi hui. "
                    "RETRY IPO LIST dabao aur phir dobara try karo."
                )
            else:
                st.info(f"IPO stocks: {len(symbols)}")
                results = run_scanner(symbols, "IPO")
                display_results(results, len(symbols), "IPO")

    with history_tab:
        symbols = get_ipo_symbols()

        if symbols:
            show_backtest_section(
                symbols, "IPO", "ipo"
            )
        else:
            st.warning(
                "IPO list load nahi hui. Current Scan tab mein "
                "RETRY IPO LIST dabakar dobara try karo."
            )
```
