# /usr/bin/python
# -*- coding: UTF-8 -*-
from math import ceil as _math_ceil

from numpy import where as _where
from pandas import DataFrame as _DataFrame, Series as _Series

__all__ = ["chunk", "concat_columns"]


# Chunk (Split) DataFrame into multiple DataFrame
def chunk(
    df: _DataFrame,
    *,
    chunk_size: int = None,
    chunk_count: int = None,
) -> list[_DataFrame]:
    """Chunk (Split) `DataFrame` into multiple `DataFrame`

    :param df: `DataFrame` to be chunked
    :param chunk_size: Size (rows) the chunked `DataFrame` should have
        - If the size of the `DataFrame` is not divisible by 'chunk_size',
          the last chunk will be smaller
        - When this parameter is provided, 'chunk_count' will be ignored

    :param chunk_count: Number of `DataFrame` to chunk into
        At least one of 'chunk_size' and 'chunk_count' must be provided
    :return: List of chunked `DataFrame`
    """

    if df.empty:
        return [df]

    # Determine the length of the original DataFrame
    _len_ = len(df)

    # If chunk_size is not provided, calculate it based on chunk_count
    if not chunk_size and chunk_count:
        chunk_size = _math_ceil(_len_ / chunk_count)

    # Validate chunk_size
    if not chunk_size:
        raise ValueError(
            "<dt_util.chunk> At least one of 'chunk_size' and 'chunk_count' must be provided"
        )

    # Split the DataFrame into chunks
    if chunk_size >= _len_:
        return [df]
    else:
        return [df[i : i + chunk_size].copy() for i in range(0, _len_, chunk_size)]


# Concatenate DataFrame columns
def concat_columns(df: _DataFrame, sep: str = "-") -> _Series:
    """Concatenate DataFrame columns

    This function is used for concatenating all the columns of a `DataFrame`
    into a single column. The columns will be concatenated in the order of
    the `DataFrame` columns, and seperated by the `sep` parameter.

    :param df: `DataFrame` to be concatenated
    :param sep: Separator between each columns
    :return: `Series` of concatenated columns

    Example:
    >>> df["concat"] = concat_columns(df[concat_columns])
    """

    if df.empty:
        raise ValueError("Input 'df' cannot be empty.")
    else:
        return df.astype(str).apply(sep.join, axis=1)


# Round half away from zero (DataFrame)
def round_away(
    data: _DataFrame | _Series,
    decimal: int = 0,
) -> _DataFrame | _Series:
    """Round a `DataFrame` or `Series` half away from zero

    :param data: Support both `DataFrame` and `Series`
        - If `DataFrame` is provided, all columns will be rounded
        - If `Series` is provided, the `Series` will be rounded

    :param decimal: Number of decimal places - `default`: `0`
    :return: Rounded `DataFrame` or `Series`

    Example - DataFrame:
    >>> columns = ["a", "b", "c"]
        df[columns] = round_away(df[columns], 2)

    Example - Series:
    >>> s = round_away(s, 2)
    """

    def rounding(s: _Series) -> _Series:
        s = s.astype(float)
        x = _where(s >= 0, 0.5, -0.5)
        return (s * factor + x).astype(int) / factor

    if data.empty:
        return data

    factor = 10**decimal
    if isinstance(data, _DataFrame):
        return data.apply(rounding)
    else:
        return rounding(data)
