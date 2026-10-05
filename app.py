import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(
page_title="NSE Swing Scanner",
page_icon="📈",
layout="wide"
)

st.title("📈 NSE Swing Scanner")
st.caption("CURRENT SCAN — Swing Low → +20% High → 2 Red Candles")

MIN_MOVE = 0.20
HISTORY_DAYS = 400

NSE_SYMBOLS = [
"20MICRONS",
"360ONE",
"3MINDIA",
"5PAISA",
"AARTIIND",
"ABB",
"ABCAPITAL",
"ABFRL",
"ACC",
"ACE",
"ADANIENT",
"ADANIGREEN",
"ADANIPORTS",
"ADANIPOWER",
"AIAENG",
"AJANTAPHARM",
"ALKEM",
"AMBER",
"AMBUJACEM",
"APARINDS",
"APLAPOLLO",
"APOLLOHOSP",
"APOLLOTYRE",
"ASHOKLEY",
"ASIANPAINT",
"ASTRAL",
"ATGL",
"AUBANK",
"AUROPHARMA",
"AXISBANK",
"BAJAJ-AUTO",
"BAJAJFINSV",
"BAJAJHLDNG",
"BAJFINANCE",
"BALKRISIND",
"BANDHANBNK",
"BANKBARODA",
"BANKINDIA",
"BEL",
"BEML",
"BERGEPAINT",
"BHARATFORG",
"BHARTIARTL",
"BHEL",
"BIOCON",
"BOSCHLTD",
"BPCL",
"BRIGADE",
"BRITANNIA",
"BSE",
"CANBK",
"CANFINHOME",
"CDSL",
"CENTRALBK",
"CESC",
"CGPOWER",
"CHAMBLFERT",
"CHOLAFIN",
"CIPLA",
"COALINDIA",
"COCHINSHIP",
"COFORGE",
"COLPAL",
"CONCOR",
"COROMANDEL",
"CROMPTON",
"CUB",
"CUMMINSIND",
"CYIENT",
"DABUR",
"DALBHARAT",
"DEEPAKNTR",
"DELHIVERY",
"DIVISLAB",
"DIXON",
"DLF",
"DMART",
"DRREDDY",
"EICHERMOT",
"EMAMILTD",
"ENDURANCE",
"ESCORTS",
"ETERNAL",
"EXIDEIND",
"FEDERALBNK",
"FINCABLES",
"FORTIS",
"GAIL",
"GESHIP",
"GICRE",
"GLENMARK",
"GODREJCP",
"GODREJIND",
"GODREJPROP",
"GRANULES",
"GRASIM",
"GSFC",
"GSPL",
"GUJGASLTD",
"HAL",
"HAVELLS",
"HCLTECH",
"HDFCAMC",
"HDFCBANK",
"HDFCLIFE",
"HEROMOTOCO",
"HFCL",
"HINDALCO",
"HINDCOPPER",
"HINDPETRO",
"HINDUNILVR",
"HINDZINC",
"HUDCO",
"ICICIBANK",
"ICICIGI",
"ICICIPRULI",
"IDBI",
"IDEA",
"IDFCFIRSTB",
"IEX",
"IGL",
"IIFL",
"INDHOTEL",
"INDIAMART",
"INDIANB",
"INDIGO",
"INDUSINDBK",
"INDUSTOWER",
"INFY",
"INOXWIND",
"IOB",
"IOC",
"IRB",
"IRCON",
"IRCTC",
"IREDA",
"IRFC",
"ITC",
"JINDALSTEL",
"JIOFIN",
"JKCEMENT",
"JSL",
"JSWENERGY",
"JSWSTEEL",
"JUBLFOOD",
"KALYANKJIL",
"KARURVYSYA",
"KEC",
"KEI",
"KFINTECH",
"KOTAKBANK",
"KPIL",
"KPRMILL",
"LALPATHLAB",
"LAURUSLABS",
"LICHSGFIN",
"LICI",
"LODHA",
"LT",
"LTIM",
"LTTS",
"LUPIN",
"M&M",
"M&MFIN",
"MAHABANK",
"MANAPPURAM",
"MARICO",
"MARUTI",
"MAXHEALTH",
"MAZDOCK",
"MCX",
"MGL",
"MOTHERSON",
"MOTILALOFS",
"MPHASIS",
"MRF",
"MUTHOOTFIN",
"NATIONALUM",
"NAUKRI",
"NBCC",
"NCC",
"NESTLEIND",
"NHPC",
"NMDC",
"NTPC",
"NYKAA",
"OBEROIRLTY",
"OFSS",
"OIL",
"ONGC",
"PAGEIND",
"PAYTM",
"PERSISTENT",
"PETRONET",
"PFC",
"PHOENIXLTD",
"PIDILITIND",
"PIIND",
"PNB",
"POLICYBZR",
"POLYCAB",
"POWERGRID",
"PRESTIGE",
"PVRINOX",
"RBLBANK",
"RECLTD",
"RELIANCE",
"RVNL",
"SAIL",
"SBICARD",
"SBILIFE",
"SBIN",
"SHREECEM",
"SHRIRAMFIN",
"SIEMENS",
"SJVN",
"SOLARINDS",
"SONACOMS",
"SRF",
"SUNPHARMA",
"SUPREMEIND",
"SUZLON",
"SWSOLAR",
"TATACHEM",
"TATACOMM",
"TATACONSUM",
"TATAELXSI",
"TATAMOTORS",
"TATAPOWER",
"TATASTEEL",
"TCS",
"TECHM",
"THERMAX",
"TIINDIA",
"TITAN",
"TORNTPHARM",
"TORNTPOWER",
"TRENT",
"TRIDENT",
"TVSMOTOR",
"UBL",
"UCOBANK",
"UNIONBANK",
"UPL",
"UTIAMC",
"VEDL",
"VGUARD",
"VOLTAS",
"WELCORP",
"WELSPUNLIV",
"WIPRO",
"YESBANK",
"ZEEL",
"ZENSARTECH",
"ZYDUSLIFE"
]

def is_red(row):
    return row["Close"] < row["Open"]

def scan_current_stock(symbol, data):

if data is None or data.empty:
    return None

data = data.copy()

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

required = ["Open", "High", "Low", "Close"]

if not all(column in data.columns for column in required):
    return None

data = data[required].copy()

for column in required:
    data[column] = pd.to_numeric(
        data[column],
        errors="coerce"
    )

data = data.dropna()
data = data.sort_index()

if len(data) < 5:
    return None

latest_swing_index = None

for i in range(len(data) - 2, 0, -1):

    current = data.iloc[i]
    previous = data.iloc[i - 1]
    next_candle = data.iloc[i + 1]

    if (
        current["Low"] < previous["Low"]
        and current["Low"] < next_candle["Low"]
    ):
        latest_swing_index = i
        break

if latest_swing_index is None:
    return None

swing_low = float(
    data.iloc[latest_swing_index]["Low"]
)

swing_date = data.index[latest_swing_index]

target_20 = swing_low * (1 + MIN_MOVE)

reached_20 = False
target_date = None
red_count = 0

first_red_date = None

for i in range(
    latest_swing_index + 1,
    len(data)
):

    candle = data.iloc[i]
    candle_date = data.index[i]

    if not reached_20:

        if candle["High"] >= target_20:

            reached_20 = True
            target_date = candle_date
            red_count = 0
            first_red_date = None

            continue

        if is_red(candle):

            red_count += 1

            if red_count >= 2:
                return None

        else:

            red_count = 0

        continue

    if is_red(candle):

        if red_count == 0:
            first_red_date = candle_date

        red_count += 1

        if red_count >= 2:

            return {
                "Symbol": symbol,
                "Swing Low": round(
                    swing_low,
                    2
                ),
                "Swing Low Date": swing_date.strftime(
                    "%Y-%m-%d"
                ),
                "+20% Level": round(
                    target_20,
                    2
                ),
                "+20% Date": target_date.strftime(
                    "%Y-%m-%d"
                ),
                "1st Red": first_red_date.strftime(
                    "%Y-%m-%d"
                ),
                "2nd Red": candle_date.strftime(
                    "%Y-%m-%d"
                ),
                "Current Close": round(
                    float(candle["Close"]),
                    2
                ),
                "Status": "MATCH"
            }

    else:

        red_count = 0
        first_red_date = None

return None

def download_stock(symbol):

try:

    end_date = datetime.now()
    start_date = (
        end_date -
        timedelta(days=HISTORY_DAYS)
    )

    data = yf.download(
        symbol + ".NS",
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

st.divider()

st.write(
"This scanner checks the latest available daily candles "
"and returns only CURRENT MATCHES."
)

if st.button(
"🔍 SCAN CURRENT NSE STOCKS",
use_container_width=True,
type="primary"
):

results = []

progress = st.progress(0)

status = st.empty()

total = len(NSE_SYMBOLS)

for number, symbol in enumerate(
    NSE_SYMBOLS,
    start=1
):

    status.write(
        "Scanning "
        + symbol
        + " — "
        + str(number)
        + "/"
        + str(total)
    )

    data = download_stock(symbol)

    result = scan_current_stock(
        symbol,
        data
    )

    if result is not None:
        results.append(result)

    progress.progress(
        number / total
    )

progress.empty()
status.empty()

st.divider()

if results:

    result_df = pd.DataFrame(results)

    st.success(
        str(len(result_df))
        + " CURRENT MATCHES FOUND"
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

else:

st.info(
    "Click the button above to scan current NSE stocks."
)
