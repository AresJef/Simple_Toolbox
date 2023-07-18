# cython: language_level=3

from math import floor
from time import time as unix_time
from datetime import datetime
from datetime import time as dt_time

cpdef long unix_timestamp(bint utc, bint ms):
    cdef:
        double ts

    if utc:
        ts = datetime.timestamp(datetime.utcnow())
    else:
        ts = unix_time()

    if ms:
        return int(ts * 100000)
    else:
        return int(ts)

cpdef seconds_to_time(long seconds):
    cdef:
        int h
        int m
        int s

    if seconds > 86400:
        return dt_time(23, 59, 59)

    else:
        h = floor(seconds / 3600)
        m = floor((seconds % 3600) / 60)
        s = floor((seconds % 3600) % 60)
        return dt_time(h, m, s)
