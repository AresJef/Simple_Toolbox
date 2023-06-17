#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from math import ceil as _math_ceil
from decimal import Decimal as _Decimal

__all__ = ["drop_duplicates", "chunk", "concat_list", "flatten", "decimal_to_float"]


# . drop duplicates
def drop_duplicates(lst: list) -> list:
    """Drop duplicates for a `list` while keeping the original order

    :param lst: list to be processed
    :return: list without duplicates in the original order
    """

    return list(dict.fromkeys(lst))


# . chunk list
def chunk(lst: list, *, chunk_size: int = None, chunk_count: int = None) -> list[list]:
    """Chunk (Split) a `list` into multiple `list`

    :param lst: `list` to be chunked
    :param chunk_size: Size (length) the chunked `list` should have
        - If the size of the `list` is not divisible by 'chunk_size',
          the last chunk will be smaller
        - When this parameter is provided, 'chunk_count' will be ignored

    :param chunk_count: Number of `list` to chunk into
        At least one of 'chunk_size' and 'chunk_count' must be provided
    :return: `list` of chunked `list`
    """

    if not lst:
        return [lst]

    # Adjust data type
    if isinstance(lst, set):
        lst = list(lst)

    # Determine the length of the original list
    _len_ = len(lst)

    # If chunk_size is not provided, calculate it based on chunk_count
    if not chunk_size and chunk_count:
        chunk_size = _math_ceil(_len_ / chunk_count)

    # Validate chunk_size
    if not chunk_size:
        raise ValueError(
            "<list_util.chunk> At least one of the parameters 'chunk_size' or 'chunk_count' must be provided"
        )

    # Split the list into chunks
    if chunk_size >= _len_:
        return [lst]
    else:
        return [lst[i : i + chunk_size] for i in range(0, _len_, chunk_size)]


# . concatenate lists
def concat_list(*lists: list | tuple | set) -> list:
    """Concatenate `lists` into a single `list`"""

    return [item for lst in lists if lst for item in lst]


# . flatten list
def flatten(lst: list | tuple | set) -> list:
    """Flatten a nested `list` / `tuple` / `set`

    :param lst: iterable to be flattened
    :return: Flattened `list`
    """

    if not isinstance(lst, (tuple, list, set)):
        return [lst]

    return [item for sublist in lst for item in flatten(sublist)]


# Convert Decimal to float from lists
def decimal_to_float(data: list[_Decimal] | list[dict]) -> list[float] | list[dict]:
    """Convert `Decimal` to `float`

    This function *only* works for two strict types of data structure:
    1. `list[Decimal]`: a `list` containing only `Decimals`
    2. `list[dict]`: a `list` of `dict`, which has certain values as `Decimal`.
        All `dict` in the `list` should have the same structure (keys and value types)

    :param data: `list[Decimal]` or `list[dict]`
    :return:
        - If `list[_Decimal]` is provided, return `list[float]`
        - If `list[dict]` is provided, return `list[dict]`
    """

    def find_decimal_keys(data: list[dict]) -> set[str]:
        return (
            {k for k, v in data[0].items() if isinstance(v, _Decimal)}
            if data
            else set()
        )

    if not data or not isinstance(data, (list, tuple)):
        return data

    elif isinstance(data[0], dict):
        if not (dec_keys := find_decimal_keys(data)):
            return data
        else:
            return [
                {k: float(v) if k in dec_keys else v for k, v in d.items()}
                for d in data
            ]

    elif isinstance(data[0], _Decimal):
        return [float(d) for d in data]

    else:
        return data
