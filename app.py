import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="NSE Swing Scanner",
    page_icon="📈",
    layout="wide"
)

st.title("📈 NSE Swing Scanner")
st.caption("Swing Low → +20% High → Reject / Match")

st.divider()


def is_red(row):
    return row["Close"] < row["Open"]


def is_green(row):
    return row["Close"] > row["Open"]


def scan_stock(df):

    df = df.copy()

    # Required columns
    required_columns = [
        "Date",
        "Open",
        "High",
        "Low",
        "Close"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        return {
            "Result": "ERROR",
            "Message": "Missing columns: " + ", ".join(missing)
        }

    # Date conversion
    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    # Numeric conversion
    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # Remove invalid rows
    df = df.dropna(
        subset=[
            "Date",
            "Open",
            "High",
            "Low",
            "Close"
        ]
    )

    # Sort oldest → newest
    df = df.sort_values(
        "Date"
    ).reset_index(drop=True)

    if len(df) < 3:
        return {
            "Result": "ERROR",
            "Message": "At least 3 candles are required."
        }

    # -----------------------------------------
    # STATE VARIABLES
    # -----------------------------------------

    active_setup = False

    swing_low = None
    swing_low_date = None

    target_20 = None
    target_date = None

    reached_20 = False

    red_count = 0

    # -----------------------------------------
    # SCAN
    # -----------------------------------------

    for i in range(1, len(df) - 1):

        current = df.iloc[i]
        previous = df.iloc[i - 1]
        next_candle = df.iloc[i + 1]

        # =====================================
        # ACTIVE SETUP
        # =====================================

        if active_setup:

            # ---------------------------------
            # BEFORE +20%
            # ---------------------------------

            if not reached_20:

                # Check +20% FIRST
                # +20% candle is NOT counted red
                if current["High"] >= target_20:

                    reached_20 = True

                    target_date = current["Date"]

                    red_count = 0

                    continue

                # Red candle
                if is_red(current):

                    red_count += 1

                    # 2 consecutive red BEFORE +20%
                    if red_count >= 2:

                        return {
                            "Result": "REJECT",
                            "Swing Low Date": swing_low_date,
                            "Swing Low": round(swing_low, 2),
                            "+20% Target": round(target_20, 2),
                            "+20% Date": None,
                            "Match Date": None
                        }

                # Green candle resets count
                else:

                    red_count = 0

                continue

            # ---------------------------------
            # AFTER +20%
            # ---------------------------------

            if reached_20:

                # Red candle
                if is_red(current):

                    red_count += 1

                    # 2 consecutive red AFTER +20%
                    if red_count >= 2:

                        return {
                            "Result": "MATCH",
                            "Swing Low Date": swing_low_date,
                            "Swing Low": round(swing_low, 2),
                            "+20% Target": round(target_20, 2),
                            "+20% Date": target_date,
                            "Match Date": current["Date"]
                        }

                # Green candle resets count
                else:

                    red_count = 0

                continue

        # =====================================
        # FIND NEW SWING LOW
        # =====================================

        if not active_setup:

            swing_low_condition = (
                current["Low"] < previous["Low"]
                and
                current["Low"] < next_candle["Low"]
            )

            if swing_low_condition:

                active_setup = True

                swing_low = current["Low"]

                swing_low_date = current["Date"]

                target_20 = swing_low * 1.20

                reached_20 = False

                target_date = None

                red_count = 0

    # =========================================
    # END OF DATA
    # =========================================

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


# =============================================
# USER INTERFACE
# =============================================

st.subheader("Upload Historical Data")

uploaded_file = st.file_uploader(
    "Upload CSV",
    type=["csv"]
)

st.info(
    "CSV must contain: Date, Open, High, Low, Close"
)


if uploaded_file:

    try:

        data = pd.read_csv(
            uploaded_file
        )

        st.write("Data preview")

        st.dataframe(
            data.head(10),
            use_container_width=True
        )

        if st.button(
            "🔍 SCAN STOCK",
            use_container_width=True
        ):

            result = scan_stock(data)

            st.divider()

            st.subheader("Scanner Result")

            if result["Result"] == "MATCH":

                st.success("✅ MATCH FOUND")

            elif result["Result"] == "REJECT":

                st.error("❌ SETUP REJECTED")

            elif result["Result"] == "ACTIVE / NO MATCH":

                st.warning("⏳ SETUP STILL ACTIVE")

            elif result["Result"] == "ERROR":

                st.error(
                    result["Message"]
                )

            result_display = pd.DataFrame(
                [result]
            )

            st.dataframe(
                result_display,
                use_container_width=True
            )

    except Exception as e:

        st.error(
            f"Error reading CSV: {e}"
        )t kiya jayega.")
