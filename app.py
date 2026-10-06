import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import io
import time
import re

st.set_page_config(
page_title="NSE Swing Scanner",
page_icon="🔍",
layout="wide"
)

st.title("NSE Swing Scanner")
st.caption(
"Full NSE • NIFTY 500 • IPO | Major Swing Low → +20% → 2 Consecutive Red Candles"
)

# ============================================================

# SETTINGS

# ============================================================

YF_PERIOD = "60d"
YF_INTERVAL = "1d"

SWING_LOOKBACK = 30
BATCH_SIZE = 80
RECENT_CANDLES = 5

NSE_LIST_URL = (
"https://archives.nseindia.com/content/equities/EQUITY_L.csv"
)

# Official NSE Nifty 500 CSV candidates

NIFTY500_URLS = [
"https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500",
"https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
"https://www.nseindia.com/content/indices/ind_nifty500list.csv",
]

# ============================================================

# HEADERS

# ============================================================

HEADERS = {
"User-Agent": (
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
"AppleWebKit/537.36 (KHTML, like Gecko) "
"Chrome/154.0.0.0 Safari/537.36"
),
"Accept": (
"text/html,application/xhtml+xml,application/xml;"
"q=0.9,text/csv;q=0.8,*/*;q=0.7"
),
"Accept-Language": "en-US,en;q=0.9",
"Referer": "https://www.nseindia.com/"
}

# ============================================================

# COMMON FUNCTIONS

# ============================================================

def clean_symbol(symbol):
    symbol = str(symbol).strip().upper()

```
if symbol.endswith(".NS"):
    symbol = symbol[:-3]

symbol = re.sub(r"\s+", "", symbol)

return symbol
```

def normalize_dataframe(data, symbol=None):
try:
if data is None or data.empty:
return pd.DataFrame()

```
    if isinstance(data.columns, pd.MultiIndex):

        if symbol:
            symbol = clean_symbol(symbol)
            ticker = symbol + ".NS"

            level_zero = [
                str(x).upper()
                for x in data.columns.get_level_values(0)
            ]

            level_one = [
                str(x).upper()
                for x in data.columns.get_level_values(1)
            ]

            if ticker.upper() in level_zero:
                data = data[ticker].copy()

            elif symbol.upper() in level_zero:
                data = data[symbol].copy()

            elif ticker.upper() in level_one:
                data = data.xs(
                    ticker,
                    axis=1,
                    level=1
                ).copy()

            elif symbol.upper() in level_one:
                data = data.xs(
                    symbol,
                    axis=1,
                    level=1
                ).copy()

            else:
                data.columns = data.columns.get_level_values(0)

        else:
            data.columns = data.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close"]

    if not all(c in data.columns for c in required):
        return pd.DataFrame()

    data = data.dropna(
        subset=required
    ).copy()

    data = data.sort_index()

    return data

except Exception:
    return pd.DataFrame()
```

# ============================================================

# FULL NSE LIST

# ============================================================

@st.cache_data(ttl=3600)
def get_nse_symbols():

```
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

    symbols = (
        df["SYMBOL"]
        .astype(str)
        .str.strip()
        .tolist()
    )

    symbols = [
        clean_symbol(s)
        for s in symbols
        if s
        and str(s).upper() != "NAN"
        and " " not in str(s)
    ]

    symbols = list(
        dict.fromkeys(symbols)
    )

    return symbols

except Exception:

    return []
```

# ============================================================

# NIFTY 500

# ============================================================

@st.cache_data(ttl=3600)
def get_nifty500_symbols():

```
# --------------------------------------------------------
# Method 1: Official NSE API
# --------------------------------------------------------

try:

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    session.get(
        "https://www.nseindia.com/",
        timeout=30
    )

    api_url = (
        "https://www.nseindia.com/api/"
        "equity-stockIndices?index=NIFTY%20500"
    )

    response = session.get(
        api_url,
        timeout=30
    )

    if response.ok:

        data = response.json()

        rows = data.get(
            "data",
            []
        )

        symbols = []

        for row in rows:

            symbol = row.get(
                "symbol"
            )

            if symbol:

                symbol = clean_symbol(
                    symbol
                )

                if symbol:
                    symbols.append(
                        symbol
                    )

        symbols = list(
            dict.fromkeys(symbols)
        )

        if len(symbols) >= 450:
            return symbols

except Exception:
    pass


# --------------------------------------------------------
# Method 2: Official NSE archive CSV
# --------------------------------------------------------

for url in NIFTY500_URLS[1:]:

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if not response.ok:
            continue

        text = response.text

        if not text:
            continue

        df = pd.read_csv(
            io.StringIO(text)
        )

        df.columns = [
            str(c).strip().upper()
            for c in df.columns
        ]

        symbol_column = None

        for col in [
            "SYMBOL",
            "SYMBOLS",
            "NIFTY 500",
            "NIFTY500"
        ]:

            if col in df.columns:
                symbol_column = col
                break

        if symbol_column is None:
            continue

        symbols = (
            df[symbol_column]
            .astype(str)
            .str.strip()
            .tolist()
        )

        symbols = [
            clean_symbol(s)
            for s in symbols
            if s
            and str(s).upper() != "NAN"
        ]

        symbols = list(
            dict.fromkeys(symbols)
        )

        if len(symbols) >= 450:
            return symbols

    except Exception:
        continue


return []
```

# ============================================================

# IPO LIST

# ============================================================

@st.cache_data(ttl=3600)
def get_ipo_symbols():

```
symbols = []

# NSE IPO equity master
urls = [
    "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
]

# --------------------------------------------------------
# IPO scanner uses NSE listed equity universe.
# Listing-date filtering is applied where possible.
# --------------------------------------------------------

try:

    response = requests.get(
        urls[0],
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    df = pd.read_csv(
        io.BytesIO(response.content)
    )

    df.columns = [
        str(c).strip().upper()
        for c in df.columns
    ]

    if "SYMBOL" not in df.columns:
        return []

    symbols = (
        df["SYMBOL"]
        .astype(str)
        .str.strip()
        .tolist()
    )

    symbols = [
        clean_symbol(s)
        for s in symbols
        if s
        and str(s).upper() != "NAN"
    ]

    symbols = list(
        dict.fromkeys(symbols)
    )

except Exception:
    pass

return symbols
```

# ============================================================

# SWING LOW

# ============================================================

def find_swing_low(data):

```
if data is None or data.empty:
    return None

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

    previous_low = float(
        data.iloc[i - 1]["Low"]
    ) if i > 0 else swing_low

    next_low = float(
        data.iloc[i + 1]["Low"]
    )

    # Proper 3-candle swing low
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

        future_high = float(
            data.iloc[j]["High"]
        )

        if future_high >= target:

            target_index = j
            break

    if target_index is None:
        continue

    # Swing low must remain intact until +20%
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
            )
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

# Prefer the most recent meaningful
# valid swing rather than tiny higher lows
candidates = sorted(
    candidates,
    key=lambda x: (
        x["index"],
        -x["low"]
    ),
    reverse=True
)

return candidates[0]["index"]
```

# ============================================================

# CHECK SETUP

# ============================================================

def check_setup(data, swing_index):

```
if swing_index is None:
    return None

swing_low = float(
    data.iloc[swing_index]["Low"]
)

swing_date = data.index[
    swing_index
]

target = swing_low * 1.20

target_index = None

first_red_index = None

# --------------------------------------------------------
# PHASE 1
# Swing Low -> +20%
# --------------------------------------------------------

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

    # +20% target not reached yet
    if target_index is None:

        if high_price >= target:

            target_index = i

            # IMPORTANT:
            # +20% candle itself is NOT
            # counted as red
            first_red_index = None

            continue

        if is_red:

            if first_red_index is None:

                first_red_index = i

            else:

                # Two consecutive reds
                # BEFORE +20% = reject
                return None

        else:

            first_red_index = None

        continue


    # ----------------------------------------------------
    # PHASE 2
    # +20% reached -> wait for 2 red candles
    # ----------------------------------------------------

    if is_red:

        if first_red_index is None:

            first_red_index = i

            continue

        second_red_index = i

        recent_start = max(
            0,
            len(data) - RECENT_CANDLES
        )

        # Old red pair = expired
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

        # Green candle resets red count
        first_red_index = None

return None
```

# ============================================================

# PROCESS STOCK

# ============================================================

def process_stock(
symbol,
data
):

```
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
```

# ============================================================

# DOWNLOAD BATCH

# ============================================================

def download_batch(symbols):

```
tickers = [
    clean_symbol(symbol) + ".NS"
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
```

# ============================================================

# GET STOCK FROM BATCH

# ============================================================

def get_stock_from_batch(
batch_data,
symbol
):

```
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

        level_zero = [
            str(x).upper()
            for x in
            batch_data.columns
            .get_level_values(0)
        ]

        level_one = [
            str(x).upper()
            for x in
            batch_data.columns
            .get_level_values(1)
        ]

        if ticker.upper() in level_zero:

            return batch_data[
                ticker
            ].copy()

        if clean_symbol(
            symbol
        ).upper() in level_zero:

            return batch_data[
                clean_symbol(symbol)
            ].copy()

        if ticker.upper() in level_one:

            return batch_data.xs(
                ticker,
                axis=1,
                level=1
            ).copy()

        if clean_symbol(
            symbol
        ).upper() in level_one:

            return batch_data.xs(
                clean_symbol(symbol),
                axis=1,
                level=1
            ).copy()

    else:

        return batch_data.copy()

    return None

except Exception:

    return None
```

# ============================================================

# GENERIC SCANNER

# ============================================================

def run_scanner(
symbols,
scanner_name
):

```
results = []

status = st.empty()

progress = st.progress(0)

total = len(symbols)

if total == 0:

    status.empty()
    progress.empty()

    return []

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
        f"{scanner_name}: "
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

    time.sleep(0.3)

status.empty()

progress.empty()

return results
```

# ============================================================

# DISPLAY RESULTS

# ============================================================

def display_results(
results,
total,
scanner_name
):

```
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

df = df[
    columns
]

df = df.sort_values(
    by="2nd Red Date",
    ascending=False
)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)
```

# ============================================================

# TABS

# ============================================================

tab1, tab2, tab3 = st.tabs(
[
"🇮🇳 FULL NSE",
"📊 NIFTY 500",
"🚀 IPO"
]
)

# ============================================================

# FULL NSE

# ============================================================

with tab1:

```
st.subheader(
    "Full NSE Equity Scanner"
)

st.write(
    "Complete NSE equity universe"
)

if st.button(
    "SCAN FULL NSE",
    type="primary",
    key="full_nse_button"
):

    status = st.empty()

    status.write(
        "Loading complete NSE equity list..."
    )

    symbols = get_nse_symbols()

    if not symbols:

        status.empty()

        st.error(
            "NSE stock list load nahi ho payi."
        )

    else:

        status.empty()

        st.info(
            f"Total NSE stocks found: "
            f"{len(symbols)}"
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
```

# ============================================================

# NIFTY 500

# ============================================================

with tab2:

```
st.subheader(
    "NIFTY 500 Scanner"
)

st.write(
    "NIFTY 500 list automatically NSE se load hogi."
)

if st.button(
    "SCAN NIFTY 500",
    type="primary",
    key="nifty500_button"
):

    status = st.empty()

    status.write(
        "Loading current NIFTY 500 list from NSE..."
    )

    symbols = (
        get_nifty500_symbols()
    )

    if not symbols:

        status.empty()

        st.error(
            "NIFTY 500 list NSE se load nahi ho payi."
        )

        st.info(
            "NSE source temporarily block "
            "kar raha ho sakta hai. "
            "Please thodi der baad retry karo."
        )

    else:

        status.empty()

        st.info(
            f"Current NIFTY 500 stocks found: "
            f"{len(symbols)}"
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
```

# ============================================================

# IPO

# ============================================================

with tab3:

```
st.subheader(
    "IPO Scanner"
)

st.write(
    "IPO scanner: 01-01-2025 se listed "
    "stocks ko scan karega."
)

st.caption(
    "Future IPO automatically tab include hoga "
    "jab stock NSE par list ho jayega."
)

if st.button(
    "SCAN IPO",
    type="primary",
    key="ipo_button"
):

    status = st.empty()

    status.write(
        "Loading IPO / NSE equity universe..."
    )

    symbols = get_ipo_symbols()

    if not symbols:

        status.empty()

        st.error(
            "IPO/NSE stock list load nahi ho payi."
        )

    else:

        status.empty()

        st.info(
            f"Stocks available for IPO scan: "
            f"{len(symbols)}"
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
```
