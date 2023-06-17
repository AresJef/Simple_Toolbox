# /usr/bin/python
# -*- coding: UTF-8 -*-
from simple_toolkits.cython_core.str_util_c import parse_float as _parse_float
from simple_toolkits.cython_core.str_util_c import parse_int as _parse_int
from simple_toolkits.cython_core.str_util_c import parce_pct as _parce_pct
from simple_toolkits.cython_core.str_util_c import replace_char as _replace_char
from simple_toolkits.cython_core.str_util_c import replace_chars as _replace_chars
from simple_toolkits.cython_core.str_util_c import (
    replace_multi_chars as _replace_multi_chars,
)
from simple_toolkits.cython_core.str_util_c import extract_alphanumeric_underscore
from simple_toolkits.cython_core.str_util_c import remove_indent as _remove_indent

__all__ = [
    "parse_float",
    "parse_int",
    "parse_pct",
    "remove_double_spaces",
    "replace_chars",
    "extract_alphanum",
]


# Parse Float
def parse_float(float_str: str, signed: bool = False) -> float:
    """Parse float from string

    Only digits, decimal point and `"-"` will be extracted from the string.
    The first decimal point will be kept and the rest will be ignored.

    :param float_str: string with floating numbers to be parsed
    :param signed: whether the float is signed or not
        - if `True`, any "-" will be treated as a negative sign
        - if `False`, "-" will be ignored

    :return: float number
    """

    try:
        return float(_parse_float(float_str, signed))
    except Exception as err:
        err.add_note(
            f"<str_util.parse_float> Failed to parse float from '{float_str}' {type(float_str)}"
        )
        raise


# Parse Int
def parse_int(int_str: str, signed: bool = False) -> int:
    """Parse int from string

    Only digits and `"-"` will be extracted from the string.

    :param int_str: string with integer numbers to be parsed
    :param signed: whether the int is signed or not
        - if `True`, any "-" will be treated as a negative sign
        - if `False`, "-" will be ignored

    :return: int number
    """

    try:
        return int(_parse_int(int_str, signed))
    except Exception as err:
        err.add_note(
            f"<str_util.parse_int> Failed to parse int from '{int_str}' {type(int_str)}"
        )
        raise


# Parse Percentage
def parse_pct(pct_str: str, signed: bool = False) -> float:
    """Parse percentage from string

    Only digits, decimal point, `"-"` and `"%"` will be extracted from the string.
    The string must contain `"%"`, else `ValueError` will be raised.
    The first decimal point will be kept and the rest will be ignored.
    After extraction, the string will be parsed as a float number, and then divided by `100`.

    :param pct_str: string with percentage to be parsed
    :param signed: whether the percentage is signed or not
    :return: percentage in float number
    """

    try:
        return _parce_pct(pct_str, signed)
    except Exception as err:
        err.add_note(
            f"<str_util.parse_pct> Failed to parse percentage from '{pct_str}' {type(pct_str)}"
        )
        raise


# Remove double spaces
def remove_double_spaces(text: str) -> str:
    """Remove all double spaces from string

    All double spaces `"  "` will be replaced with single space `" "`.
    And `strip()` will be performed at the end.

    :param text: string containing double spaces `"  "`to be processed
    :return: string with all double spaces removed
    """

    return _replace_char(text, "  ", " ", True).strip()


# Replace chars from string
def replace_chars(
    text: str,
    repl_char: str,
    *targ_chars: str,
    iterative: bool = True,
) -> str:
    """Replace all target chars with replacement char

    All target chars will be replaced with replacement char.

    :param text: string containing target chars to be replaced
    :param repl_char: replacement char
    :param targ_chars: target chars to be replaced
    :param iterative: whether to iterate until no target chars are found
        This can be usefull for replacement such as "  " -> " "
    :return: string with all target chars replaced with replacement char
    """

    return _replace_chars(text, repl_char, targ_chars, iterative)


# Replace multiple chars from string
def replace_multi_chars(
    text: str,
    *repls: tuple[str, str],
    iterative: bool = False,
) -> str:
    """Replace multiple chars from string

    The repls of each tuple should contains two strings, the first should
    be the `TARGET` charater, and the second should be the `REPLACEMENT`.

    :param text: string containing target chars to be replaced
    :param repls: tuples containing target chars and replacement
    :param iterative: whether to iterate until no target chars are found
        This can be usefull for replacement such as "  " -> " "
    :return: string with all target chars replaced with replacement char
    """

    return _replace_multi_chars(text, repls, iterative)


# Extract [a-zA-Z0-9_] from string
def extract_alphanum(text: str) -> str:
    """Extract all [a-zA-Z0-9_] from string

    :param text: string containing characters to be extracted
    :return: string with all [a-zA-Z0-9_] extracted
    """

    return extract_alphanumeric_underscore(text)


# Remove indent
def remove_indent(text: str) -> str:
    """Remove indents from text

    Remove all leading indents from text, while keeping the relative indents
    between lines. A simple cythonized version of `textwrap.dedent` to minor
    speed improvement.

    :param text: text to be processed
    :return: text with indents removed
    """

    return _remove_indent(text)
