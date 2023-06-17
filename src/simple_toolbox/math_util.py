#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from decimal import Decimal as _Decimal
from simple_toolbox.cython_core.math_util_c import round_away as _round_away


# Round half away from zero
def round_away(num: str | int | float | _Decimal, decimal: int = 0) -> float:
    """Round a number half away from zero

    :param num: Number to be rounded
    :param decimal: Number of decimal places - `default`: `0`

    :return: Rounded number
    """

    num, factor = _round_away(float(num), decimal)
    return num / factor
