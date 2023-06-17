cimport cython
from re import sub as _re_sub
from re import compile as _re_compile
from re import MULTILINE as _RE_MULTILINE

### Extract Float
cdef str _extract_float(str float_str, bint signed):
    cdef:
        str neg = "-"
        str dot = "."
        str nul = ""
        str char
        str res = ""

    if signed and neg in float_str:
        res += "-"

    for char in float_str:
        if dot == char and dot not in res and res != nul and res != neg:
            res += dot
        elif char.isdigit():
            res += char

    return res

cpdef double parse_float(str float_str, bint signed) except *:
    if not float_str:
        raise ValueError("provided float_str is empty")

    cdef str res = _extract_float(float_str, signed)
    return float(res)

### Extract Int
cdef str _extract_int(str int_str, bint signed):
    cdef:
        str neg = "-"
        str nul = ""
        str char
        str res = ""

    if signed and neg in int_str:
        res += "-"

    for char in int_str:
        if char.isdigit():
            res += char

    return res

cpdef long long parse_int(str int_str, bint signed) except *:
    if not int_str:
        raise ValueError("provided int_str is empty")

    cdef str res = _extract_int(int_str, signed)
    return int(res)

### Parse Percentage
cpdef double parce_pct(str pct_str, bint signed) except *:
    cdef plus = "%"
    if not pct_str or plus not in pct_str:
        raise ValueError("provided pct_str doesn't contain '%'")

    cdef str res = _extract_float(pct_str, signed)
    return float(res) / 100

### Relpace Charactors for string
cdef str _replace_char_iterative(str string, str targ_char, str repl_char):
    while targ_char in string:
        string = string.replace(targ_char, repl_char)
    return string

cpdef str replace_char(str string, str targ_char, str repl_char, bint iterative):
    if not string:
        return string
    elif iterative:
        return _replace_char_iterative(string, targ_char, repl_char)
    else:
        return string.replace(targ_char, repl_char)

@cython.boundscheck(False)  # Deactivate bounds checking
cpdef str replace_chars(str string, str repl_char, tuple targ_chars, bint iterative):
    cdef str targ_char

    if not string or not targ_chars:
        return string
    elif iterative:
        for targ_char in targ_chars:
            string = _replace_char_iterative(string, targ_char, repl_char)
        return string
    else:
        for targ_char in targ_chars:
            string = string.replace(targ_char, repl_char)
        return string

@cython.boundscheck(False)  # Deactivate bounds checking
cpdef str replace_multi_chars(str string, tuple repls, bint iterative):
    cdef:
        str targ_char
        str repl_char

    if not string or not repls:
        return string
    elif iterative:
        for targ_char, repl_char in repls:
            string = _replace_char_iterative(string, targ_char, repl_char)
        return string
    else:
        for targ_char, repl_char in repls:
            string = string.replace(targ_char, repl_char)
        return string

### Extract [a-zA-Z0-9_] from string
@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing
cpdef str extract_alphanumeric_underscore(str string):
    cdef:
        bytes input_bytes = string.encode('utf-8')
        bytearray output_bytes = bytearray()
        long input_length = len(input_bytes)
        long i
        char c

    for i in range(input_length):
        c = input_bytes[i]
        if (c >= b'A' and c <= b'Z') or (c >= b'a' and c <= b'z') or (c >= b'0' and c <= b'9') or c == b'_':
            output_bytes.append(c)
    return output_bytes.decode('utf-8')

### Reomve indent
_ONLY_WHITESPACE_RE = _re_compile("^[ \t]+$", _RE_MULTILINE)
_LEAD_WHITESPACE_RE = _re_compile("(^[ \t]*)(?:[^ \t\n])", _RE_MULTILINE)
@cython.wraparound(False)   # Deactivate negative indexing
cpdef str remove_indent(str text):
    cdef:
        str margin = "$NONE$"
        str indent
        int i
        str x
        str y

    # Look for the longest leading string of spaces and tabs common to all lines.
    text = _ONLY_WHITESPACE_RE.sub("", text)
    cdef list indents = _LEAD_WHITESPACE_RE.findall(text)
    for indent in indents:
        if margin == "$NONE$":
            margin = indent

        # Current line more deeply indented than previous winner:
        # no change (previous winner is still on top).
        elif indent.startswith(margin):
            pass

        # Current line consistent with and no deeper than previous winner:
        # it's the new winner.
        elif margin.startswith(indent):
            margin = indent

        # Find the largest common whitespace between current line and previous
        # winner.
        else:
            for i, (x, y) in enumerate(zip(margin, indent)):
                if x != y:
                    margin = margin[:i]
                    break

    if margin != "$NONE$":
        text = _re_sub(r"(?m)^" + margin, "", text)
    return text

