from typing import Any

import numpy as np


def dms_to_dd(dms_value: Any) -> float:
    """
    Utility function to convert degrees minutes seconds coordinates to decimal degrees.

    Args:
        dms_value: A degrees-minutes-seconds location value.

    Returns: The same value in decimal degrees.
    """

    # if the dms_value passed is nan, return nan
    try:
        # convert decimal degree value to string value
        if not isinstance(dms_value, str):
            dms_value = str(int(dms_value))
    except ValueError:
        return np.nan

    # break the dd_value string into 3 parts
    if dms_value[0] == "-":
        # if the string less than 7 digits, left pad it
        if len(dms_value) < 7:
            dms_value = dms_value.ljust(7, "0")
        degrees = int(dms_value[:3])
        minutes = int(dms_value[3:5])
        seconds = int(dms_value[-2:])
    else:
        # if the string less than 6 digits, left pad it
        if len(dms_value) < 6:
            dms_value = dms_value.ljust(6, "0")
        degrees = int(dms_value[:2])
        minutes = int(dms_value[2:4])
        seconds = int(dms_value[-2:])
    print(dms_value, degrees, minutes, seconds)
    dd_value = degrees + (minutes / 60) + (seconds / 3600)
    return round(dd_value, 8)
