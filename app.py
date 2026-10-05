import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(
page_title="NSE Swing Scanner",
page_icon="📈",
layout="wide"
)

st.title("📈 NSE Swing Scanner")
st.caption("CURRENT SCAN — Swing Low → +20% High → 2 Red Candles")

# ---------------------------------------------------------

# SETTINGS

# ---------------------------------------------------------

MIN_MOVE = 0.20
RED_CANDLES_REQUIRED = 2
HISTORY_DAYS = 400

# ---------------------------------------------------------

# NSE STOCK UNIVERSE

# ---------------------------------------------------------

NSE_SYMBOLS = [
"20MICRONS", "21STCENMGM", "360ONE", "3IINFOTECH",
"3MINDIA", "5PAISA", "63MOONS", "AARTIDRUGS",
"AARTIIND", "AAVAS", "ABB", "ABBOTINDIA",
"ABCAPITAL", "ABFRL", "ACC", "ACE",
"ACI", "ADANIENT", "ADANIGREEN", "ADANIPORTS",
"ADANIPOWER", "ADFFOODS", "ADORWELD", "AIAENG",
"AJANTAPHARM", "AKUMS", "ALEMBICLTD", "ALKEM",
"ALKYLAMINE", "ALLCARGO", "AMARAJABAT", "AMBER",
"AMBUJACEM", "ANANDRATHI", "ANANTRAJ", "ANGELONE",
"ANUP", "APARINDS", "APLAPOLLO", "APLLTD",
"APOLLOHOSP", "APOLLOTYRE", "ARVIND", "ASHOKLEY",
"ASIANPAINT", "ASTERDM", "ASTRAL", "ATGL",
"ATUL", "AUBANK", "AUROPHARMA", "AVANTIFEED",
"AXISBANK", "BAJAJ-AUTO", "BAJAJFINSV", "BAJAJHLDNG",
"BAJFINANCE", "BALKRISIND", "BALRAMCHIN", "BANDHANBNK",
"BANKBARODA", "BANKINDIA", "BATAINDIA", "BAYERCROP",
"BEL", "BEML", "BERGEPAINT", "BHARATFORG",
"BHARTIARTL", "BHEL", "BIOCON", "BIRLACORPN",
"BLUESTARCO", "BOSCHLTD", "BPCL", "BRIGADE",
"BRITANNIA", "BSE", "BSOFT", "CANBK",
"CANFINHOME", "CAPLIPOINT", "CARBORUNIV", "CASTROLIND",
"CDSL", "CEATLTD", "CENTRALBK", "CENTURYPLY",
"CESC", "CGPOWER", "CHALET", "CHAMBLFERT",
"CHEMPLASTS", "CHENNPETRO", "CHOLAFIN", "CIPLA",
"CLEAN", "COALINDIA", "COCHINSHIP", "COFORGE",
"COLPAL", "CONCOR", "COROMANDEL", "CREDITACC",
"CROMPTON", "CUB", "CUMMINSIND", "CYIENT",
"DABUR", "DALBHARAT", "DATAPATTNS", "DCMSHRIRAM",
"DEEPAKFERT", "DEEPAKNTR", "DELHIVERY", "DELTACORP",
"DEVYANI", "DHANI", "DIVISLAB", "DIXON",
"DLF", "DMART", "DRREDDY", "EASEMYTRIP",
"ECLERX", "EICHERMOT", "EIDPARRY", "EIHOTEL",
"ELGIEQUIP", "EMAMILTD", "EMCURE", "ENDURANCE",
"ENGINERSIN", "EQUITASBNK", "ERIS", "ESCORTS",
"ETERNAL", "EXIDEIND", "FACT", "FEDERALBNK",
"FINCABLES", "FINEORG", "FINPIPE", "FIVESTAR",
"FLUOROCHEM", "FORTIS", "FSL", "GAIL",
"GESHIP", "GICRE", "GLAND", "GLENMARK",
"GMRAIRPORT", "GNFC", "GODFRYPHLP", "GODREJAGRO",
"GODREJCP", "GODREJIND", "GODREJPROP", "GRANULES",
"GRAPHITE", "GRASIM", "GREAVESCOT", "GREENPANEL",
"GRINDWELL", "GRINFRA", "GSFC", "GSPL",
"GUJGASLTD", "HAL", "HAPPSTMNDS", "HAVELLS",
"HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE",
"HEADSUP", "HEG", "HEROMOTOCO", "HFCL",
"HINDALCO", "HINDCOPPER", "HINDPETRO", "HINDUNILVR",
"HINDZINC", "HOMEFIRST", "HONASA", "HUDCO",
"ICICIBANK", "ICICIGI", "ICICIPRULI", "IDBI",
"IDEA", "IDFCFIRSTB", "IEX", "IGL",
"IIFL", "INDHOTEL", "INDIACEM", "INDIAMART",
"INDIANB", "INDIGO", "INDIGOPNTS", "INDUSINDBK",
"INDUSTOWER", "INFY", "INOXWIND", "INTELLECT",
"IOB", "IOC", "IPCALAB", "IRB",
"IRCON", "IRCTC", "IREDA", "IRFC",
"ITC", "ITI", "J&KBANK", "JBCHEPHARM",
"JINDALSAW", "JINDALSTEL", "JIOFIN", "JKCEMENT",
"JKLAKSHMI", "JKPAPER", "JMFINANCIL", "JSL",
"JSWENERGY", "JSWSTEEL", "JUBLFOOD", "JUSTDIAL",
"JYOTHYLAB", "KAJARIACER", "KALYANKJIL", "KANSAINER",
"KARURVYSYA", "KEC", "KEI", "KFINTECH",
"KIRLOSBROS", "KIRLOSENG", "KNRCON", "KOTAKBANK",
"KPIGREEN", "KPIL", "KPRMILL", "KRBL",
"LALPATHLAB", "LATENTVIEW", "LAURUSLABS", "LEMONTREE",
"LICHSGFIN", "LICI", "LINDEINDIA", "LODHA",
"LT", "LTIM", "LTTS", "LUPIN",
"M&M", "M&MFIN", "MAHABANK", "MAHINDCIE",
"MANAPPURAM", "MANKIND", "MARICO", "MARUTI",
"MAXHEALTH", "MAZDOCK", "MCX", "MEDANTA",
"MEDPLUS", "METROBRAND", "MFSL", "MGL",
"MHRIL", "MINDACORP", "MMTC", "MOIL",
"MOTHERSON", "MOTILALOFS", "MPHASIS", "MRF",
"MUTHOOTFIN", "NATCOPHARM", "NATIONALUM", "NAUKRI",
"NAVINFLUOR", "NBCC", "NCC", "NESTLEIND",
"NHPC", "NIACL", "NLCINDIA", "NMDC",
"NSLNISP", "NTPC", "NUVOCO", "NYKAA",
"OBEROIRLTY", "OFSS", "OIL", "OLECTRA",
"ONGC", "PAGEIND", "PATANJALI", "PAYTM",
"PCBL", "PEL", "PERSISTENT", "PETRONET",
"PFC", "PFIZER", "PGEL", "PHOENIXLTD",
"PIDILITIND", "PIIND", "PNB", "PNCINFRA",
"POLICYBZR", "POLYCAB", "POWERGRID", "POWERMECH",
"PPLPHARMA", "PRAJIND", "PRESTIGE", "PRICOLLTD",
"PRIVISCL", "PVRINOX", "RADICO", "RAILTEL",
"RAIN", "RAJESHEXPO", "RALLIS", "RAMCOCEM",
"RBLBANK", "RECLTD", "REDINGTON", "RELIANCE",
"RHIM", "RITES", "RKFORGE", "ROUTE",
"RVNL", "SAIL", "SAMMAANCAP", "SANDUMA",
"SBFC", "SBICARD", "SBILIFE", "SBIN",
"SCHAEFFLER", "SCI", "SHREECEM", "SHRIRAMFIN",
"SIEMENS", "SJVN", "SKFINDIA", "SOLARINDS",
"SONACOMS", "SONATSOFTW", "SRF", "STARHEALTH",
"SUMICHEM", "SUNPHARMA", "SUNTV", "SUPREMEIND",
"SURYAROSNI", "SUZLON", "SWANENERGY", "SWSOLAR",
"TATACHEM", "TATACOMM", "TATACONSUM", "TATAELXSI",
"TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS",
"TECHM", "TECHNO", "THERMAX", "TIINDIA",
"TIMKEN", "TITAN", "TORNTPHARM", "TORNTPOWER",
"TRENT", "TRIDENT", "TRIVENI", "TVSMOTOR",
"UBL", "UCOBANK", "UFLEX", "UNIONBANK",
"UNITDSPR", "UPL", "USHAMART", "UTIAMC",
"VAIBHAVGBL", "VAKRANGEE", "VARROC", "VEDL",
"VGUARD", "VIJAYA", "VINATIORGA", "VIPIND",
"VOLTAS", "WELCORP", "WELSPUNLIV", "WESTLIFE",
"WHIRLPOOL", "WIPRO", "WOCKPHARMA", "YESBANK",
"ZEEL", "ZENSARTECH", "ZENTEC", "ZYDUSLIFE"
]

# ---------------------------------------------------------

# RED CANDLE

# ---------------------------------------------------------

def is_red(row):
    return row["Close"] < row["Open"]

# ---------------------------------------------------------

# SCAN CURRENT SETUP

# ---------------------------------------------------------

def scan_current_stock(symbol, df):

```
if df is None or df.empty:
    return None

df = df.copy()

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

required = ["Open", "High", "Low", "Close"]

for col in required:
    if col not in df.columns:
        return None

df = df[required].copy()

for col in required:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna()

if len(df) < 5:
    return None

df = df.sort_index()

# -----------------------------------------------------
# We only care about the LATEST setup.
# Start from the newest candle and work backwards.
# -----------------------------------------------------

active_setup = False
swing_index = None

# Find latest valid swing low
for i in range(len(df) - 2, 0, -1):

    current = df.iloc[i]
    previous = df.iloc[i - 1]
    next_candle = df.iloc[i + 1]

    if (
        current["Low"] < previous["Low"]
        and current["Low"] < next_candle["Low"]
    ):
        swing_index = i
        break

if swing_index is None:
    return None

swing_low = float(df.iloc[swing_index]["Low"])
swing_date = df.index[swing_index]
target_20 = swing_low * 1.20

red_count = 0
reached_20 = False
target_date = None

# -----------------------------------------------------
# Evaluate candles AFTER swing low
# -----------------------------------------------------

for i in range(swing_index + 1, len(df)):

    candle = df.iloc[i]

    # -----------------------------------------------
    # BEFORE +20%
    # -----------------------------------------------

    if not reached_20:

        # +20% candle itself is NOT red-counted
        if candle["High"] >= target_20:

            reached_20 = True
            target_date = df.index[i]
            red_count = 0

            continue

        if is_red(candle):

            red_count += 1

            if red_count >= RED_CANDLES_REQUIRED:

                return None

        else:

            red_count = 0

        continue

    # -----------------------------------------------
    # AFTER +20%
    # -----------------------------------------------

    if reached_20:

        if is_red(candle):

            red_count += 1

            if red_count >= RED_CANDLES_REQUIRED:

                return {
                    "Symbol": symbol,
                    "Swing Low": round(swing_low, 2),
                    "Swing Low Date": swing_date.strftime("%Y-%m-%d"),
                    "+20% Level": round(target_20, 2),
                    "+20% Date": target_date.strftime("%Y-%m-%d"),
                    "1st Red": (
                        df.index[i - 1].strftime("%Y-%m-%d")
                        if i >= 1 else ""
                    ),
                    "2nd Red": df.index[i].strftime("%Y-%m-%d"),
                    "Current Close": round(float(candle["Close"]), 2),
                    "Status": "MATCH"
                }

        else:

            red_count = 0

return None
```

# ---------------------------------------------------------

# DOWNLOAD DATA

# ---------------------------------------------------------

def download_stock(symbol):

```
ticker = symbol + ".NS"

try:

    end_date = datetime.now()
    start_date = end_date - timedelta(days=HISTORY_DAYS)

    data = yf.download(
        ticker,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False
    )

    return data

except Exception:

    return None
```

# ---------------------------------------------------------

# APP

# ---------------------------------------------------------

st.divider()

st.write(
"Scan the latest available NSE daily candles and find stocks "
"whose CURRENT setup matches your rules."
)

if st.button(
"🔍 SCAN CURRENT NSE STOCKS",
use_container_width=True,
type="primary"
):

```
results = []
progress = st.progress(0)
status_text = st.empty()

total = len(NSE_SYMBOLS)

for count, symbol in enumerate(NSE_SYMBOLS, start=1):

    status_text.write(
        f"Scanning {symbol} — {count}/{total}"
    )

    data = download_stock(symbol)

    result = scan_current_stock(symbol, data)

    if result is not None:
        results.append(result)

    progress.progress(count / total)

status_text.empty()
progress.empty()

st.divider()

if results:

    result_df = pd.DataFrame(results)

    st.success(
        f"🎯 {len(result_df)} CURRENT MATCHES FOUND"
    )

    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "No CURRENT MATCH found."
    )
```

else:

```
st.info(
    "Click SCAN CURRENT NSE STOCKS to start the current scan."
)
```

