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

    # =====================================================
    # SCAN FORWARD FROM SWING LOW
    # =====================================================

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

            # -------------------------------------------------
            # FIRST CHECK RED CANDLES
            # -------------------------------------------------

            if is_red:

                if first_red_index is None:

                    first_red_index = i

                else:

                    # -----------------------------------------
                    # TWO CONSECUTIVE RED CANDLES BEFORE +20%
                    # = INVALID SETUP
                    # -----------------------------------------

                    return None

            else:

                # Red sequence broken
                first_red_index = None

            # -------------------------------------------------
            # NOW CHECK +20%
            # -------------------------------------------------

            if high_price >= target:

                target_index = i

                # +20% candle itself is NOT red #1
                first_red_index = None

                continue

            continue

        # =================================================
        # AFTER +20%
        # =================================================

        if is_red:

            # First red candle
            if first_red_index is None:

                first_red_index = i

            else:

                # Second consecutive red candle
                second_red_index = i

                # Must be recent
                if (
                    second_red_index
                    >= len(data) - 5
                ):

                    return {

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

                # Start looking for another pair
                first_red_index = i

        else:

            # Consecutive red sequence broken
            first_red_index = None

    return None
