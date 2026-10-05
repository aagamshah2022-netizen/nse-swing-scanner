import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="NSE Swing Scanner",
    page_icon="📈",
    layout="wide"
)

st.title("NSE Swing Scanner")
st.caption("Swing Low -> +20% High -> Reject / Match")


def is_red(row):
    return row["Close"] < row["Open"]


def scan_stock(df):

    required = ["Date", "Open", "High", "Low", "Close"]

    missing = [col for col in required if col not in df.columns]

    if missing:
        return {
            "Result": "ERROR",
            "Message": "Missing columns: " + ", ".join(missing)
        }

    df = df.copy()

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=["Date", "Open", "High", "Low", "Close"]
    )

    df = df.sort_values("Date").reset_index(drop=True)

    if len(df) < 3:
        return {
            "Result": "ERROR",
            "Message": "At least 3 candles are required."
        }

    active_setup = False
    swing_low = None
    swing_low_date = None
    target_20 = None
    target_date = None
    reached_20 = False
    red_count = 0

    for i in range(1, len(df) - 1):

        current = df.iloc[i]
        previous = df.iloc[i - 1]
        next_candle = df.iloc[i + 1]

        if active_setup:

            if not reached_20:

                if current["High"] >= target_20:

                    reached_20 = True
                    target_date = current["Date"]
                    red_count = 0

                    continue

                if is_red(current):

                    red_count += 1

                    if red_count >= 2:

                        return {
                            "Result": "REJECT",
                            "Swing Low Date": swing_low_date,
                            "Swing Low": round(swing_low, 2),
                            "+20% Target": round(target_20, 2),
                            "+20% Date": None,
                            "Match Date": None
                        }

                else:

                    red_count = 0

                continue

            if reached_20:

                if is_red(current):

                    red_count += 1

                    if red_count >= 2:

                        return {
                            "Result": "MATCH",
                            "Swing Low Date": swing_low_date,
                            "Swing Low": round(swing_low, 2),
                            "+20% Target": round(target_20, 2),
                            "+20% Date": target_date,
                            "Match Date": current["Date"]
                        }

                else:

                    red_count = 0

                continue

        if not active_setup:

            swing_low_condition = (
                current["Low"] < previous["Low"]
                and current["Low"] < next_candle["Low"]
            )

            if swing_low_condition:

                active_setup = True

                swing_low = current["Low"]
                swing_low_date = current["Date"]
                target_20 = swing_low * 1.20

                reached_20 = False
                target_date = None
                red_count = 0

    if active_setup:

        return {
            "Result": "ACTIVE / NO MATCH",
            "Swing Low Date": swing_low_date,
            "Swing Low": round(swing_low, 2),
            "+20% Target": round(target_20, 2),
            "+20% Date": target_date,
            "Match Date": None
        }

    return {
        "Result": "NO SETUP",
        "Swing Low Date": None,
        "Swing Low": None,
        "+20% Target": None,
        "+20% Date": None,
        "Match Date": None
    }


st.subheader("Upload Historical Data")

uploaded_file = st.file_uploader(
    "Upload CSV",
    type=["csv"]
)

st.info(
    "CSV columns required: Date, Open, High, Low, Close"
)


if uploaded_file is not None:

    try:

        data = pd.read_csv(uploaded_file)

        st.subheader("Data Preview")

        st.dataframe(
            data.head(10),
            use_container_width=True
        )

        if st.button(
            "SCAN STOCK",
            use_container_width=True
        ):

            result = scan_stock(data)

            st.divider()

            st.subheader("Scanner Result")

            if result["Result"] == "MATCH":
                st.success("MATCH FOUND")

            elif result["Result"] == "REJECT":
                st.error("SETUP REJECTED")

            elif result["Result"] == "ACTIVE / NO MATCH":
                st.warning("SETUP STILL ACTIVE")

            elif result["Result"] == "ERROR":
                st.error(result["Message"])

            st.dataframe(
                pd.DataFrame([result]),
                use_container_width=True
            )

    except Exception as e:

        st.error(
            "Error reading CSV: " + str(e)
        )
