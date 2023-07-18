# cython: language_level=3

cpdef tuple round_away(double num, int decimals):
    cdef: 
        int factor = 10**decimals

    if num >= 0:
        return int(num * factor + 0.5), factor
    else:
        return int(num * factor - 0.5), factor
