def check_setup(data, swing_index):

    swing_low = float(data.iloc[swing_index]["Low"])
    swing_date = data.index[swing_index]

    target = swing_low * 1.20

    target_index = None
    first_red_index = None

    # =====================================================
    # SCAN FORWARD FROM SWING LOW
    # =====================================================

    for i in range(swing_index + 1, len(data)):

        open_price = float(data.iloc[i]["Open"])
        high_price = float(data.iloc[i]["High"])
        close_price = float(data.iloc[i]["Close"])

        is_red = close_price < open_price

        # =================================================
        # BEFORE +20%
        # =================================================

        if target_index is None:

            # ---------------------------------------------
            # FIRST CHECK +20%
            # ---------------------------------------------
            # The candle which FIRST reaches +20%
            # is NOT counted as a red candle.
            # ---------------------------------------------

            if high_price >= target:

                target_index = i
                first_red_index = None
                continue

            # ---------------------------------------------
            # +20% NOT REACHED YET
            # Check for 2 consecutive red candles
            # ---------------------------------------------

            if is_red:

                if first_red_index is None:

                    # First red candle
                    first_red_index = i

                else:

                    # -------------------------------------
                    # TWO CONSECUTIVE RED CANDLES
                    # BEFORE +20%
                    #
                    # SETUP INVALID
                    # -------------------------------------

                    return None

            else:

                # Green candle breaks red sequence
                first_red_index = None

            continue

        # =================================================
        # AFTER +20%
        # =================================================

        if is_red:

            # ---------------------------------------------
            # FIRST RED CANDLE AFTER +20%
            # ---------------------------------------------

            if first_red_index is None:

                first_red_index = i

            else:

                # -----------------------------------------
                # SECOND CONSECUTIVE RED CANDLE
                # -----------------------------------------

                second_red_index = i

                # Must be recent
                if second_red_index >= len(data) - 5:

                    return {
                        "Swing Low": round(swing_low, 2),

                        "Swing Low Date":
                            swing_date.strftime("%Y-%m-%d"),

                        "+20% Level":
                            round(target, 2),

                        "+20% Date":
                            data.index[target_index].strftime(
                                "%Y-%m-%d"
                            ),

                        "1st Red Date":
                            data.index[first_red_index].strftime(
                                "%Y-%m-%d"
                            ),

                        "2nd Red Date":
                            data.index[second_red_index].strftime(
                                "%Y-%m-%d"
                            ),

                        "2nd Red Close":
                            round(close_price, 2)
                    }

                # Pair was too old.
                # Start checking from this red candle again.
                first_red_index = i

        else:

            # Green candle breaks consecutive red sequence
            first_red_index = None

    return None
