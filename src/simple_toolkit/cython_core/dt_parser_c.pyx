from io import StringIO
from math import copysign
from decimal import Decimal
from string import ascii_uppercase
from re import compile as re_compile
from calendar import monthrange, isleap
from six import text_type, integer_types
from datetime import tzinfo as dt_tzinfo
from datetime import datetime, timedelta, date
from time import localtime, tzname as t_tzname
from operator import gt as ops_gt, lt as ops_lt
from dateutil import tz as _tz
from dateutil.relativedelta import relativedelta


# weekday -------------------------------------------------------------------------------------
cdef tuple _WEEKDAYS_STR = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")

cdef class Weekday:
    cdef:
        int weekday
        int n

    def __init__(self, weekday, n = -1):
        self.weekday = weekday
        self.n = n

    def __call__(self, n):
        if n == self.n:
            return self
        else:
            return self.__class__(self.weekday, n)

    def __eq__(self, other):
        try:
            if self.weekday != other.weekday or self.n != other.n:
                return False
            else:
                return True
        except AttributeError:
            return False

    def __hash__(self):
        return hash((self.weekday, self.n))

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        s = _WEEKDAYS_STR[self.weekday]
        if self.n == -1:
            return s
        else:
            return "%s(%+d)" % (s, self.n)

    def __bool__(self):
        return self.weekday != -1

cdef Weekday NONE = Weekday(-1)
cdef Weekday MO = Weekday(0)
cdef Weekday TU = Weekday(1)
cdef Weekday WE = Weekday(2)
cdef Weekday TH = Weekday(3)
cdef Weekday FR = Weekday(4)
cdef Weekday SA = Weekday(5)
cdef Weekday SU = Weekday(6)
cdef dict _WEEKDAYS_DICT = {
    0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA, 6: SU,
    MO: MO, TU: TU, WE: WE, TH: TH, FR: FR, SA: SA, SU: SU,
}

# ctimedelta ----------------------------------------------------------------------------------
cdef tuple _YEARDAY_IDX = (31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 366)

cdef class ctimedelta:
    """The ctimedelta type is designed to be applied to an existing datetime and
    can replace specific components of that datetime, or represents an interval
    of time.

    It is based on the specification of the excellent work done by M.-A. Lemburg
    in his
    `mx.DateTime <https://www.egenix.com/products/python/mxBase/mxDateTime/>`_ extension.
    However, notice that this type does *NOT* implement the same algorithm as
    his work. Do *NOT* expect it to behave like mx.DateTime's counterpart.

    There are two different ways to build a ctimedelta instance. The
    first one is passing it two date/datetime classes::

        ctimedelta(datetime1, datetime2)

    The second one is passing it any number of the following keyword arguments::

        ctimedelta(arg1=x,arg2=y,arg3=z...)

        year, month, day, hour, minute, second, microsecond:
            Absolute information (argument is singular); adding or subtracting a
            ctimedelta with absolute information does not perform an arithmetic
            operation, but rather REPLACES the corresponding value in the
            original datetime with the value(s) in ctimedelta.

        years, months, weeks, days, hours, minutes, seconds, microseconds:
            Relative information, may be negative (argument is plural); adding
            or subtracting a ctimedelta with relative information performs
            the corresponding arithmetic operation on the original datetime value
            with the information in the ctimedelta.

        weekday:
            One of the weekday instances (MO, TU, etc) available in the
            ctimedelta module. These instances may receive a parameter N,
            specifying the Nth weekday, which could be positive or negative
            (like MO(+1) or MO(-2)). Not specifying it is the same as specifying
            +1. You can also use an integer, where 0=MO. This argument is always
            relative e.g. if the calculated date is already Monday, using MO(1)
            or MO(-1) won't change the day. To effectively make it absolute, use
            it in combination with the day argument (e.g. day=1, MO(1) for first
            Monday of the month).

        leapdays:
            Will add given days to the date found, if year is a leap
            year, and the date found is post 28 of february.

        yearday, nlyearday:
            Set the yearday or the non-leap year day (jump leap days).
            These are converted to day/month/leapdays information.

    There are relative and absolute forms of the keyword
    arguments. The plural is relative, and the singular is
    absolute. For each argument in the order below, the absolute form
    is applied first (by setting each attribute to that value) and
    then the relative form (by adding the value to the attribute).

    The order of attributes considered when this ctimedelta is
    added to a datetime is:

    1. Year
    2. Month
    3. Day
    4. Hours
    5. Minutes
    6. Seconds
    7. Microseconds

    Finally, weekday is applied, using the rule described above.

    For example

    >>> from datetime import datetime
    >>> from dateutil.ctimedelta import ctimedelta, MO
    >>> dt = datetime(2018, 4, 9, 13, 37, 0)
    >>> delta = ctimedelta(hours=25, day=1, weekday=MO(1))
    >>> dt + delta
    datetime.datetime(2018, 4, 2, 14, 37)

    First, the day is set to 1 (the first of the month), then 25 hours
    are added, to get to the 2nd day and 14th hour, finally the
    weekday is applied, but since the 2nd is already a Monday there is
    no effect.
    """
    
    cdef:
        int years
        int months
        int days
        int leapdays
        int hours
        int minutes
        int seconds
        int microseconds
        int year
        int month
        int day
        Weekday weekday
        int hour
        int minute
        int second
        int microsecond
        bint _has_time


    def __init__(
        self,
        dt1 =None,
        dt2 = None,
        years: int = 0,
        months: int = 0,
        days: int = 0,
        leapdays: int = 0,
        weeks: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
        year: int = -1,
        month: int = -1,
        day: int = -1,
        weekday: int = -1,
        yearday: int = -1,
        nlyearday: int = -1,
        hour: int = -1,
        minute: int = -1,
        second: int = -1,
        microsecond: int = -1,
    ):
        if dt1 and dt2:
            # Initiate relative information
            self.years = 0
            self.months = 0
            self.days = 0
            self.leapdays = 0
            self.hours = 0
            self.minutes = 0
            self.seconds = 0
            self.microseconds = 0
            
            # Initiate absolute information
            self.year = -1
            self.month = -1
            self.day = -1
            self.weekday = NONE
            self.hour = -1
            self.minute = -1
            self.second = -1
            self.microsecond = -1
            self._has_time = False

            # Initiate with two datetimes
            self._init_with_dts(dt1, dt2)
        else:
            # Initiate Relative information
            self.years = years
            self.months = months
            self.days = days + weeks * 7
            self.leapdays = leapdays
            self.hours = hours
            self.minutes = minutes
            self.seconds = seconds
            self.microseconds = microseconds

            # Initiate absolute information
            self.year = year
            self.month = month
            self.day = day
            self.weekday = _WEEKDAYS_DICT.get(weekday, NONE)
            self.hour = hour
            self.minute = minute
            self.second = second
            self.microsecond = microsecond
            self._has_time = False

            # Initiate with arguments
            self._init_with_args(yearday, nlyearday)
        self._init_fix()

    cpdef _init_with_dts(self, object dt1, object dt2):
        cdef:
            int months
            int dt1_year
            int dt1_month
            int dt2_year
            int dt2_month
            int increment
            object dtm
            object delta
            int delta_seconds
            int delta_days
            int delta_microseconds

        # datetime is a subclass of date. So both must be date
        if not (isinstance(dt1, date) and isinstance(dt2, date)):
            raise TypeError("ctimedelta only diffs datetime/date")

        # We allow two dates, or two datetimes, so we coerce them to be of the same type
        if isinstance(dt1, datetime) != isinstance(dt2, datetime):
            if not isinstance(dt1, datetime):
                dt1 = datetime.fromordinal(dt1.toordinal())
            elif not isinstance(dt2, datetime):
                dt2 = datetime.fromordinal(dt2.toordinal())

        # Get year / month delta between the two datetimes
        dt1_year = dt1.year
        dt1_month = dt1.month
        dt2_year = dt2.year
        dt2_month = dt2.month
        months = (dt1_year - dt2_year) * 12 + (dt1_month - dt2_month)
        self._set_months(months)

        # Remove the year/month delta so the timedelta is just well-defined
        # time units (seconds, days and microseconds)
        dtm = self.__add__(dt2)

        # If we've overshot our target, make an adjustment
        if dt1 < dt2:
            compare = ops_gt
            increment = 1
        else:
            compare = ops_lt
            increment = -1

        while compare(dt1, dtm):
            months += increment
            self._set_months(months)
            dtm = self.__add__(dt2)

        # Get the timedelta between the "months-adjusted" date and dt1
        delta = dt1 - dtm
        delta_seconds = delta.seconds
        delta_days = delta.days
        self.seconds = delta_seconds + delta_days * 86400
        delta_microseconds = delta.microseconds
        self.microseconds = delta_microseconds

    cpdef _init_with_args(self, int yearday, int nlyearday):
        cdef:
            int yday = 0
            int idx
            int ydays

        if nlyearday != -1:
            yday = nlyearday
        elif yearday != -1:
            yday = yearday
            if yearday > 59:
                self.leapdays = -1

        if yday:
            for idx, ydays in enumerate(_YEARDAY_IDX):
                if yday <= ydays:
                    self.month = idx + 1
                    if idx == 0:
                        self.day = yday
                    else:
                        self.day = yday - _YEARDAY_IDX[idx - 1]
                    break
            else:
                raise ValueError("invalid year day (%d)" % yday)

    cpdef _init_fix(self):
        cdef:
            int s
            int div_
            int mod_

        if abs(self.microseconds) > 999999:
            s = int(copysign(1, self.microseconds))
            div_, mod_ = divmod(self.microseconds * s, 1000000)
            self.microseconds = mod_ * s
            self.seconds += div_ * s

        if abs(self.seconds) > 59:
            s = int(copysign(1, self.seconds))
            div_, mod_ = divmod(self.seconds * s, 60)
            self.seconds = mod_ * s
            self.minutes += div_ * s

        if abs(self.minutes) > 59:
            s = int(copysign(1, self.minutes))
            div_, mod_ = divmod(self.minutes * s, 60)
            self.minutes = mod_ * s
            self.hours += div_ * s

        if abs(self.hours) > 23:
            s = int(copysign(1, self.hours))
            div_, mod_ = divmod(self.hours * s, 24)
            self.hours = mod_ * s
            self.days += div_ * s

        if abs(self.months) > 11:
            s = int(copysign(1, self.months))
            div_, mod_ = divmod(self.months * s, 12)
            self.months = mod_ * s
            self.years += div_ * s

        if (
            self.hours
            or self.minutes
            or self.seconds
            or self.microseconds
            or self.hour != -1
            or self.minute != -1
            or self.second != -1
            or self.microsecond != -1
        ):
            self._has_time = True
        else:
            self._has_time = True

    # Setters / getters
    @property
    def has_time(self):
        return self._has_time

    @property
    def weeks(self):
        return self._get_weeks(self.days)

    @weeks.setter
    def weeks(self, value):
        self.days = self.days - (self.weeks * 7) + value * 7

    cpdef int _get_weeks(self, int days):
        return int(days / 7.0)

    cpdef _set_months(self, int months):
        cdef:
            int s
            int div_
            int mod_

        self.months = months
        if abs(self.months) > 11:
            s = int(copysign(1, self.months))
            div_, mod_ = divmod(self.months * s, 12)
            self.months = mod_ * s
            self.years = div_ * s
        else:
            self.years = 0

    # Additions
    def __add__(object left_o, object right_o):
        type_l = type(left_o)
        type_r = type(right_o)

        if type_r == ctimedelta:
            if type_l == datetime:
                return right_o._add_datetime(left_o)

            elif type_l == date:
                if right_o.has_time:
                    left_o = datetime.fromordinal(left_o.toordinal())
                return right_o._add_datetime(left_o)

            elif type_l == ctimedelta:
                return left_o._add_ctimedelta(right_o)

            elif type_l == relativedelta:
                return right_o._add_relativedelta(left_o)
                
            elif type_l == timedelta:
                return right_o._add_timedelta(left_o)

        elif type_l == ctimedelta:
            if type_r == datetime:
                return left_o._add_datetime(right_o)

            elif type_r == date:
                if left_o.has_time:
                    right_o = datetime.fromordinal(right_o.toordinal())
                return left_o._add_datetime(right_o)

            elif type_r == relativedelta:
                return left_o._add_relativedelta(right_o)

            elif type_r == timedelta:
                return left_o._add_timedelta(right_o)

        return NotImplemented

    cpdef _add_datetime(self, object other):
        cdef:
            int other_year
            int other_month
            int other_day
            int year
            int month
            int day
            int days
            dict repl
            str attr
            int value
            object ret
            int weekday
            int nth
            int jumpdays
            int ret_weekday

        # Adjustment for year
        if self.year in (-1, 0):
            other_year = other.year
            year = other_year + self.years
        else:
            year = self.year + self.years

        # Adjustmet for month
        other_month = other.month
        month = other_month if self.month in (-1, 0) else self.month
        if self.months:
            assert 1 <= abs(self.months) <= 12
            month += self.months
            if month > 12:
                year += 1
                month -= 12
            elif month < 1:
                year -= 1
                month += 12

        # Adjustment for day
        if self.day in (-1, 0):
            other_day = other.day
            day = min(monthrange(year, month)[1], other_day)
        else:
            day = min(monthrange(year, month)[1], self.day)

        # Construct replacements
        repl = {"year": year, "month": month, "day": day}
        for attr, value in [
            ("hour", self.hour),
            ("minute", self.minute),
            ("second", self.second),
            ("microsecond", self.microsecond),
        ]:
            if value != -1:
                repl[attr] = value

        # Adjustment for leap
        days = self.days
        if self.leapdays and month > 2 and isleap(year):
            days += self.leapdays

        # Replace datetime values & add timedelta
        ret = other.replace(**repl) + timedelta(
            days=days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
            microseconds=self.microseconds,
        )

        # Adjustment for weekday
        if self.weekday:
            weekday = self.weekday.weekday
            nth = 1 if self.weekday.n in (-1, 0) else self.weekday.n
            jumpdays = (abs(nth) - 1) * 7
            ret_weekday = ret.weekday()
            if nth > 0:
                jumpdays += (7 - ret_weekday + weekday) % 7
            else:
                jumpdays += (ret_weekday - weekday) % 7
                jumpdays *= -1
            ret += timedelta(days=jumpdays)

        # Return
        return ret

    cpdef ctimedelta _add_ctimedelta(self, ctimedelta other):
        return self.__class__(
                years=other.years + self.years,
                months=other.months + self.months,
                days=other.days + self.days,
                hours=other.hours + self.hours,
                minutes=other.minutes + self.minutes,
                seconds=other.seconds + self.seconds,
                microseconds=other.microseconds + self.microseconds,
                leapdays=other.leapdays or self.leapdays,
                year=(other.year if other.year != -1 else self.year),
                month=(other.month if other.month != -1 else self.month),
                day=(other.day if other.day != -1 else self.day),
                weekday=(other.weekday if other.weekday else self.weekday),
                hour=(other.hour if other.hour != -1 else self.hour),
                minute=(other.minute if other.minute != -1 else self.minute),
                second=(other.second if other.second != -1 else self.second),
                microsecond=(
                    other.microsecond if other.microsecond != -1 else self.microsecond
                ),
            )

    cpdef ctimedelta _add_relativedelta(self, object other):
        cdef:
            int years = other.years
            int months = other.months
            int days = other.days
            int hours = other.hours
            int minutes = other.minutes
            int seconds = other.seconds
            int microseconds = other.microseconds
            int leapdays = other.leapdays

        return self.__class__(
                years=years + self.years,
                months=months + self.months,
                days=days + self.days,
                hours=hours + self.hours,
                minutes=minutes + self.minutes,
                seconds=seconds + self.seconds,
                microseconds=microseconds + self.microseconds,
                leapdays=leapdays or self.leapdays,
                year=(other.year if other.year is not None else self.year),
                month=(other.month if other.month is not None else self.month),
                day=(other.day if other.day is not None else self.day),
                weekday=(other.weekday if other.weekday is not None else self.weekday),
                hour=(other.hour if other.hour is not None else self.hour),
                minute=(other.minute if other.minute is not None else self.minute),
                second=(other.second if other.second is not None else self.second),
                microsecond=(
                    other.microsecond
                    if other.microsecond is not None
                    else self.microsecond
                ),
            )

    cpdef ctimedelta _add_timedelta(self, object other):
        cdef:
            int days = other.days
            int seconds = other.seconds
            int microseconds = other.microseconds

        return self.__class__(
                years=self.years,
                months=self.months,
                days=self.days + days,
                hours=self.hours,
                minutes=self.minutes,
                seconds=self.seconds + seconds,
                microseconds=self.microseconds + microseconds,
                leapdays=self.leapdays,
                year=self.year,
                month=self.month,
                day=self.day,
                weekday=self.weekday,
                hour=self.hour,
                minute=self.minute,
                second=self.second,
                microsecond=self.microsecond,
            )

    # Subtraction
    def __sub__(object left_o, object right_o):
        type_l = type(left_o)
        type_r = type(right_o)

        if type_r == ctimedelta:
            if type_l == datetime:
                return right_o.__neg__()._add_datetime(left_o)

            elif type_l == date:
                if right_o.has_time:
                    left_o = datetime.fromordinal(left_o.toordinal())
                return right_o.__neg__()._add_datetime(left_o)

            elif type_l == ctimedelta:
                return left_o._add_ctimedelta(right_o.__neg__())

            elif type_l == relativedelta:
                return right_o.__neg__()._add_relativedelta(left_o)
                
            elif type_l == timedelta:
                return right_o.__neg__()._add_timedelta(left_o)

        elif type_l == ctimedelta:
            if type_r == relativedelta:
                return left_o._sub_relativedelta(right_o)

            elif type_r == timedelta:
                return left_o._sub_timedelta(right_o)

        return NotImplemented  # In case the other object defines __rsub__

    cpdef ctimedelta _sub_relativedelta(self, object other):
        cdef:
            int years = other.years
            int months = other.months
            int days = other.days
            int hours = other.hours
            int minutes = other.minutes
            int seconds = other.seconds
            int microseconds = other.microseconds
            int leapdays = other.leapdays


        return self.__class__(
                years=self.years - years,
                months=self.months - months,
                days=self.days - days,
                hours=self.hours - hours,
                minutes=self.minutes - minutes,
                seconds=self.seconds - seconds,
                microseconds=self.microseconds - microseconds,
                leapdays=self.leapdays or leapdays,
                year=(self.year if self.year is not None else other.year),
                month=(self.month if self.month is not None else other.month),
                day=(self.day if self.day is not None else other.day),
                weekday=(self.weekday if self.weekday else other.weekday),
                hour=(self.hour if self.hour is not None else other.hour),
                minute=(self.minute if self.minute is not None else other.minute),
                second=(self.second if self.second is not None else other.second),
                microsecond=(
                    self.microsecond
                    if self.microsecond is not None
                    else other.microsecond
                ),
            )

    cpdef ctimedelta _sub_timedelta(self, object other):
        cdef:
            int days = other.days
            int seconds = other.seconds
            int microseconds = other.microseconds

        return self.__class__(
                years=self.years,
                months=self.months,
                days=self.days - days,
                hours=self.hours,
                minutes=self.minutes,
                seconds=self.seconds - seconds,
                microseconds=self.microseconds - microseconds,
                leapdays=self.leapdays,
                year=self.year,
                month=self.month,
                day=self.day,
                weekday=self.weekday,
                hour=self.hour,
                minute=self.minute,
                second=self.second,
                microsecond=self.microsecond,
            )

    # Multiplication and division
    def __mul__(object left_o, object right_o):
        try:
            if isinstance(left_o, ctimedelta):
                return left_o._mul(float(right_o))
            else:
                return right_o._mul(float(left_o))
        except Exception:
            return NotImplemented

    def __div__(object left_o, object right_o):
        try:
            if isinstance(left_o, ctimedelta):
                return left_o._mul(1 / float(right_o))
            else:
                return right_o._mul(1 / float(left_o))
        except Exception:
            return NotImplemented

    def __truediv__(object left_o, object right_o):
        try:
            if isinstance(left_o, ctimedelta):
                return left_o._mul(1 / float(right_o))
            else:
                return right_o._mul(1 / float(left_o))
        except Exception:
            return NotImplemented

    cpdef ctimedelta _mul(self, float f):
        return self.__class__(
            years=int(self.years * f),
            months=int(self.months * f),
            days=int(self.days * f),
            hours=int(self.hours * f),
            minutes=int(self.minutes * f),
            seconds=int(self.seconds * f),
            microseconds=int(self.microseconds * f),
            leapdays=self.leapdays,
            year=self.year,
            month=self.month,
            day=self.day,
            weekday=self.weekday,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
        )


    # Absolute & Negation
    def __abs__(self):
        return self._abs()

    cpdef ctimedelta _abs(self):
        return self.__class__(
            years=abs(self.years),
            months=abs(self.months),
            days=abs(self.days),
            hours=abs(self.hours),
            minutes=abs(self.minutes),
            seconds=abs(self.seconds),
            microseconds=abs(self.microseconds),
            leapdays=self.leapdays,
            year=self.year,
            month=self.month,
            day=self.day,
            weekday=self.weekday,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
        )

    def __neg__(self):
        return self._neg()

    cpdef ctimedelta _neg(self):
        return self.__class__(
            years=-self.years,
            months=-self.months,
            days=-self.days,
            hours=-self.hours,
            minutes=-self.minutes,
            seconds=-self.seconds,
            microseconds=-self.microseconds,
            leapdays=self.leapdays,
            year=self.year,
            month=self.month,
            day=self.day,
            weekday=self.weekday,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
        )

    # Boolean
    def __bool__(self):
        return self._bool()

    def __nonzero__(self):
        return self._bool()

    cpdef bint _bool(self):
        return not (
            not self.years
            and not self.months
            and not self.days
            and not self.hours
            and not self.minutes
            and not self.seconds
            and not self.microseconds
            and not self.leapdays
            and self.year == -1
            and self.month == -1
            and self.day == -1
            and self.weekday
            and self.hour == -1
            and self.minute == -1
            and self.second == -1
            and self.microsecond == -1
        )

    def __eq__(object left_o, object right_o):
        type_l = type(left_o)
        type_r = type(right_o)

        if type_l == ctimedelta and type_r == ctimedelta:
            return left_o._eq_ctimedelta(right_o)

        elif type_r == relativedelta:
            return left_o._eq_relativedelta(right_o)

        elif type_l == relativedelta:
            return right_o._eq_relativedelta(left_o)
            
        return NotImplemented

    cpdef bint _eq_ctimedelta(self, ctimedelta other):
        if self.weekday or other.weekday:
            if not self.weekday or not other.weekday:
                return False
            if self.weekday.weekday != other.weekday.weekday:
                return False
            n1, n2 = self.weekday.n, other.weekday.n
            if n1 != n2 and not (n1 in (-1, 0, 1) and n2 in (-1, 0, 1)):
                return False
        
        return (
            self.years == other.years
            and self.months == other.months
            and self.days == other.days
            and self.hours == other.hours
            and self.minutes == other.minutes
            and self.seconds == other.seconds
            and self.microseconds == other.microseconds
            and self.leapdays == other.leapdays
            and self.year == other.year
            and self.month == other.month
            and self.day == other.day
            and self.hour == other.hour
            and self.minute == other.minute
            and self.second == other.second
            and self.microsecond == other.microsecond
        )

    cpdef bint _eq_relativedelta(self, object other):
        if self.weekday or other.weekday:
            if not self.weekday or not other.weekday:
                return False
            if self.weekday.weekday != other.weekday.weekday:
                return False
            n1, n2 = self.weekday.n, other.weekday.n
            if n1 != n2 and not ((n1 in (-1, 0, 1)) and (not n2 or n2 == 1)):
                return False

        return (
            self.years == other.years
            and self.months == other.months
            and self.days == other.days
            and self.hours == other.hours
            and self.minutes == other.minutes
            and self.seconds == other.seconds
            and self.microseconds == other.microseconds
            and self.leapdays == other.leapdays
            and self.year == (-1 if other.year is None else other.year)
            and self.month == (-1 if other.month is None else other.month)
            and self.day == (-1 if other.day is None else other.day)
            and self.hour == (-1 if other.hour is None else other.hour)
            and self.minute == (-1 if other.minute is None else other.minute)
            and self.second == (-1 if other.second is None else other.second)
            and self.microsecond
            == (-1 if other.microsecond is None else other.microsecond)
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(
            (
                self.weekday,
                self.years,
                self.months,
                self.days,
                self.hours,
                self.minutes,
                self.seconds,
                self.microseconds,
                self.leapdays,
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute,
                self.second,
                self.microsecond,
            )
        )

    def __repr__(self):
        return self._gen_repr()

    cpdef str _gen_repr(self):
        cdef:
            list reprs = []
            str attr
            int value

        for attr, value in [
            ("years", self.years),
            ("months", self.months),
            ("days", self.days),
            ("leapdays", self.leapdays),
            ("hours", self.hours),
            ("minutes", self.minutes),
            ("seconds", self.seconds),
            ("microseconds", self.microseconds),
        ]:
            if value:
                reprs.append("{attr}={value:+g}".format(attr=attr, value=value))

        for attr, value in [
            ("year", self.year),
            ("month", self.month),
            ("day", self.day),
        ]:
            if value != -1:
                reprs.append("{attr}={value}".format(attr=attr, value=repr(value)))

        if self.weekday:
            reprs.append("weekday={value}".format(value=repr(self.weekday)))

        for attr, value in [
            ("hour", self.hour),
            ("minute", self.minute),
            ("second", self.second),
            ("microsecond", self.microsecond),
        ]:
            if value != -1:
                reprs.append("{attr}={value}".format(attr=attr, value=repr(value)))

        return "{classname}({attrs})".format(
            classname=self.__class__.__name__, attrs=", ".join(reprs)
        )

# timelex --------------------------------------------------------------------------------
cdef _SPLIT_DECIMAL_RE = re_compile(r"([.,])")

cdef class timelex:
    cdef:
        object instream
        object _split_decimal
        list charstack
        list tokenstack
        bint eof

    def __init__(self, instream):
        if isinstance(instream, (bytes, bytearray)):
            instream = instream.decode()

        if isinstance(instream, text_type):
            instream = StringIO(instream)

        elif getattr(instream, "read", None) is None:
            raise TypeError(
                "Parser must be a string or character stream, not "
                "{itype}".format(itype=instream.__class__.__name__)
            )

        self.instream = instream
        self._split_decimal = _SPLIT_DECIMAL_RE
        self.charstack = []
        self.tokenstack = []
        self.eof = False

    cpdef str get_token(self):
        """This function breaks the time string into lexical units (tokens), which
        can be parsed by the parser. Lexical units are demarcated by changes in
        the character set, so any continuous string of letters is considered
        one unit, any continuous string of numbers is considered one unit.

        The main complication arises from the fact that dots ('.') can be used
        both as separators (e.g. "Sep.20.2009") or decimal points (e.g.
        "4:30:21.447"). As such, it is necessary to read the full context of
        any dot-separated strings before breaking it into tokens; as such, this
        function maintains a "token stack", for when the ambiguous context
        demands that multiple tokens be parsed at once.
        """

        cdef:
            bint seenl
            str token
            str state
            str nextchar
            str token_i
            list token_split

        if self.tokenstack:
            return self.tokenstack.pop(0)

        seenl = False
        token = None
        state = None

        while not self.eof:
            # We only realize that we've reached the end of a token when we
            # find a character that's not part of the current token - since
            # that character may be part of the next token, it's stored in the
            # charstack.
            if self.charstack:
                nextchar = self.charstack.pop(0)
            else:
                nextchar = self.instream.read(1)
                while nextchar == "\x00":
                    nextchar = self.instream.read(1)

            if not nextchar:
                self.eof = True
                break
            elif not state:
                # First character of the token - determines if we're starting
                # to parse a word, a number or something else.
                token = nextchar
                if nextchar.isalpha():
                    state = "a"
                elif nextchar.isdigit():
                    state = "0"
                elif nextchar.isspace():
                    token = " "
                    break  # emit token
                else:
                    break  # emit token
            elif state == "a":
                # If we've already started reading a word, we keep reading
                # letters until we find something that's not part of a word.
                seenl = True
                if nextchar.isalpha():
                    token += nextchar
                elif nextchar == ".":
                    token += nextchar
                    state = "a."
                else:
                    self.charstack.append(nextchar)
                    break  # emit token
            elif state == "0":
                # If we've already started reading a number, we keep reading
                # numbers until we find something that doesn't fit.
                if nextchar.isdigit():
                    token += nextchar
                elif nextchar == "." or (nextchar == "," and len(token) >= 2):
                    token += nextchar
                    state = "0."
                else:
                    self.charstack.append(nextchar)
                    break  # emit token
            elif state == "a.":
                # If we've seen some letters and a dot separator, continue
                # parsing, and the tokens will be broken up later.
                seenl = True
                if nextchar == "." or nextchar.isalpha():
                    token += nextchar
                elif nextchar.isdigit() and token[-1] == ".":
                    token += nextchar
                    state = "0."
                else:
                    self.charstack.append(nextchar)
                    break  # emit token
            elif state == "0.":
                # If we've seen at least one dot separator, keep going, we'll
                # break up the tokens later.
                if nextchar == "." or nextchar.isdigit():
                    token += nextchar
                elif nextchar.isalpha() and token[-1] == ".":
                    token += nextchar
                    state = "a."
                else:
                    self.charstack.append(nextchar)
                    break  # emit token

        if not token:
            return token

        if state in ("a.", "0.") and (seenl or token.count(".") > 1 or token[-1] in ".,"):
            token_split = self._split_decimal.split(token)
            token = token_split[0]
            for token_i in token_split[1:]:
                if token_i:
                    self.tokenstack.append(token_i)

        if state == "0." and token.count(".") == 0:
            token = token.replace(",", ".")

        return token

    def __iter__(self):
        return self

    def __next__(self):
        token = self.get_token()
        if token is None:
            raise StopIteration

        return token

    def next(self):
        return self.__next__()

    @classmethod
    def split(cls, s: str) -> list[str]:
        return list(cls(s))

# dtresult -----------------------------------------------------------------------------
cdef class dtresult:
    cdef:
        int year
        int month
        int day
        int weekday
        int hour
        int minute
        int second
        int microsecond
        str tzname
        int tzoffset
        int ampm
        bint century_specified
        dict _values

    def __init__(self) -> None:
        self.year: int = -1
        self.month: int = -1
        self.day: int = -1
        self.weekday: int = -1
        self.hour: int = -1
        self.minute: int = -1
        self.second: int = -1
        self.microsecond: int = -1
        self.tzname: str = ""
        self.tzoffset: int = -999999
        self.ampm: int = -1
        self.century_specified: bool = False
        self._values: dict = {}

    @property
    def values(self) -> dict:
        return self._values

    cpdef set_year(self, int year):
        if year != -1:
            self.year = year
            self._values["year"] = year

    cpdef set_month(self, int month):
        if month != -1:
            self.month = month
            self._values["month"] = month

    cpdef set_day(self, int day):
        if day != -1:
            self.day = day
            self._values["day"] = day

    cpdef set_weekday(self, int weekday):
        if weekday != -1:
            self.weekday = weekday
            self._values["weekday"] = weekday

    cpdef set_hour(self, int hour):
        if hour != -1:
            self.hour = hour
            self._values["hour"] = hour

    cpdef set_minute(self, int minute):
        if minute != -1:
            self.minute = minute
            self._values["minute"] = minute

    cpdef set_second(self, int second):
        if second != -1:
            self.second = second
            self._values["second"] = second

    cpdef set_microsecond(self, int microsecond):
        if microsecond != -1:
            self.microsecond = microsecond
            self._values["microsecond"] = microsecond

    cpdef set_tzname(self, str tzname):
        if tzname:
            self.tzname = tzname
            self._values["tzname"] = tzname

    cpdef set_tzoffset(self, int tzoffset):
        if tzoffset != -999999:
            self.tzoffset = tzoffset
            self._values["tzoffset"] = tzoffset

    cpdef set_ampm(self, int ampm):
        if ampm != -1:
            self.ampm = ampm
            self._values["ampm"] = ampm

    cpdef set_century_specified(self, bint century_specified):
        if century_specified:
            self.century_specified = True
            self._values["century_specified"] = century_specified

    def __repr__(self):
        return self._values.__repr__()

    def __len__(self):
        return len(self._values)

    def __bool__(self):
        return len(self._values) > 0

# parserinfo ---------------------------------------------------------------------------
cdef list _JUMP = [" ",".",",",";","-","/","'","at","on","and","ad","m","t","of","st",
                   "nd","rd","th","年","月","日"]
cdef list _UTCZONE = ["UTC", "GMT", "Z", "z"]
cdef list _PERTAIN = ["of"]
cdef list _WEEKDAYS = [
    ("Mon", "Monday", "星期一", "周一"),
    ("Tue", "Tuesday", "星期二", "周二"),
    ("Wed", "Wednesday", "星期三", "周三"),
    ("Thu", "Thursday", "星期四", "周四"),
    ("Fri", "Friday", "星期五", "周五"),
    ("Sat", "Saturday", "星期六", "周六"),
    ("Sun", "Sunday", "星期日", "周日"),
]
cdef list _MONTHS = [
    ("jan", "january", "januar", "janvier", "gennaio", "enero", "一月"),
    ("feb", "february", "februar", "février", "febbraio", "febrero", "二月"),
    ("mar", "march", "märz", "mars", "marzo", "三月"),
    ("apr", "april", "avril", "aprile", "abril", "四月"),
    ("may", "mai", "maggio", "mayo", "五月"),
    ("jun", "june", "juni", "juin", "giugno", "junio", "六月"),
    ("jul", "july", "juli", "juillet", "luglio", "julio", "七月"),
    ("aug", "august", "août", "agosto", "八月"),
    ("sept", "september", "septembre", "settembre", "septiembre", "九月"),
    ("oct", "october", "oktober", "octobre", "ottobre", "octubre", "十月"),
    ("nov", "november", "novembre", "novembre", "noviembre", "十一月"),
    ("dec", "december", "dezember", "décembre", "dicembre", "diciembre", "十二月"),
]
cdef list _HMS = [
    ("h", "hour", "hours", "小时", "时"),
    ("m", "minute", "minutes", "分钟", "分"),
    ("s", "second", "seconds", "秒"),
]
cdef list _AMPM = [
    ("am", "a", "上午"),
    ("pm", "p", "下午"),
]
cdef dict _TZOFFSET = {}

cdef class parserinfo:
    """Class which handles what inputs are accepted. Subclass this to customize
    the language and acceptable values for each parameter.

    :param dayfirst:
        Whether to interpret the first value in an ambiguous 3-integer date
        (e.g. 01/05/09) as the day (``True``) or month (``False``). If
        ``yearfirst`` is set to ``True``, this distinguishes between YDM
        and YMD. Default is ``False``.

    :param yearfirst:
        Whether to interpret the first value in an ambiguous 3-integer date
        (e.g. 01/05/09) as the year. If ``True``, the first number is taken
        to be the year, otherwise the last number is taken to be the year.
        Default is ``False``.
    """

    cdef:
        bint dayfirst
        bint yearfirst
        set _jump
        set _utczone
        set _pertain
        dict _weekdays
        dict _months
        dict _hms
        dict _ampm
        dict _tzoffset
        int _year
        int _century

    def __init__(self, dayfirst: bool = False, yearfirst: bool = False):
        self.dayfirst: bool = dayfirst
        self.yearfirst: bool = yearfirst
        self._jump: set[str] = self._convert_to_set(_JUMP)
        self._utczone: set[str] = self._convert_to_set(_UTCZONE)
        self._pertain: set[str] = self._convert_to_set(_PERTAIN)
        self._weekdays: dict[str, int] = self._convert_to_dict(_WEEKDAYS)
        self._months: dict[str, int] = self._convert_to_dict(_MONTHS)
        self._hms: dict[str, int] = self._convert_to_dict(_HMS)
        self._ampm: dict[str, int] = self._convert_to_dict(_AMPM)
        self._tzoffset: dict[str, int] = _TZOFFSET
        self._year: int = localtime().tm_year
        self._century: int = self._year // 100 * 100

    cpdef _convert_to_set(self, list lst):
        cdef set s = set()
        for i in lst:
            s.add(i.lower())
        return s

    cpdef _convert_to_dict(self, list lst):
        cdef:
            dict dct = {}
            int i

        for i, v in enumerate(lst):
            if isinstance(v, (tuple, list)):
                for v in v:
                    dct[v.lower()] = i
            else:
                dct[v.lower()] = i
        return dct

    cpdef bint jump(self, str name):
        return name.lower() in self._jump
    
    cpdef bint utczone(self, str name):
        return name.lower() in self._utczone

    cpdef bint pertain(self, str name):
        return name.lower() in self._pertain

    cpdef int weekday(self, str name):
        return self._weekdays.get(name.lower(), -1)

    cpdef int month(self, str name):
        cdef int v = self._months.get(name.lower(), -2)
        return v + 1

    cpdef int hms(self, str name):
        return self._hms.get(name.lower(), -1)

    cpdef int ampm(self, str name):
        return self._ampm.get(name.lower(), -1)

    cpdef int tzoffset(self, str name):
        if name in self._utczone:
            return 0
        return self._tzoffset.get(name, -999999)

    cpdef int convertyear(self, int year, bint century_specified = False):
        """Converts two-digit years to year within [-50, 49]
        range of self._year (current local time)
        """

        # Function contract is that the year is always positive
        assert year >= 0

        if year < 100 and not century_specified:
            # assume current century to start
            year += self._century
            if year >= self._year + 50:  # if too far in future
                year -= 100
            elif year < self._year - 50:  # if too far in past
                year += 100

        return year

    cpdef bint validate(self, dtresult res):
        # move to info
        if res.year != -1:
            res.set_year(self.convertyear(res.year, res.century_specified))

        if (res.tzoffset == 0 and not res.tzname) or (
            res.tzname == "Z" or res.tzname == "z"
        ):
            res.set_tzname("UTC")
            res.set_tzoffset(0)
        elif res.tzoffset != 0 and res.tzname and self.utczone(res.tzname):
            res.set_tzoffset(0)
        return True

# ymd -----------------------------------------------------------------------------------
cdef class YMD:
    cdef:
        bint century_specified
        int dstridx
        int mstridx
        int ystridx
        list _lst

    def __init__(self):
        self.century_specified: bool = False
        self.dstridx: int = -1
        self.mstridx: int = -1
        self.ystridx: int = -1
        self._lst: list[int] = []

    @property
    def has_year(self):
        return self.ystridx != -1

    @property
    def has_month(self):
        return self.mstridx != -1

    @property
    def has_day(self):
        return self.dstridx != -1

    cpdef bint could_be_day(self, int val):
        cdef:
            int month
            int year

        if self.has_day:
            return False

        elif not self.has_month:
            return 1 <= val <= 31

        elif not self.has_year:
            # Be permissive, assume leap year
            month = self._lst[self.mstridx]
            return 1 <= val <= monthrange(2000, month)[1]

        else:
            month = self._lst[self.mstridx]
            year = self._lst[self.ystridx]
            return 1 <= val <= monthrange(year, month)[1]

    cpdef append(self, val, str label = ""):
        if hasattr(val, "__len__"):
            if val.isdigit() and len(val) > 2:
                self.century_specified = True
                if label not in ("", "Y"):  # pragma: no cover
                    raise ValueError(label)
                label = "Y"
        elif val > 100:
            self.century_specified = True
            if label not in ("", "Y"):  # pragma: no cover
                raise ValueError(label)
            label = "Y"

        self._lst.append(int(val))

        if label == "M":
            if self.has_month:
                raise ValueError("Month is already set")
            self.mstridx = len(self._lst) - 1
        elif label == "D":
            if self.has_day:
                raise ValueError("Day is already set")
            self.dstridx = len(self._lst) - 1
        elif label == "Y":
            if self.has_year:
                raise ValueError("Year is already set")
            self.ystridx = len(self._lst) - 1

    cpdef _resolve_from_stridxs(self, dict strids):
        """Try to resolve the identities of year/month/day elements using
        ystridx, mstridx, and dstridx, if enough of these are specified.
        """

        cdef:
            tuple strid_vals
            list miss
            list keys
            int i
            str v
            int year
            int month
            int day

        if len(self._lst) == 3 and len(strids) == 2:
            # we can back out the remaining stridx value
            miss = []
            strid_vals = tuple(strids.values())
            for i in range(3):
                if i not in strid_vals:
                    miss.append(i)

            keys = []
            for v in ("y", "m", "d"):
                if v not in strids:
                    keys.append(v)

            assert len(miss) == len(keys) == 1
            strids[keys[0]] = miss[0]

        assert len(self._lst) == len(strids)  # otherwise this should not be called
        year = self._lst[strids["y"]] if "y" in strids else -1
        month = self._lst[strids["m"]] if "m" in strids else -1
        day = self._lst[strids["d"]] if "d" in strids else -1
        return year, month, day

    cpdef resolve_ymd(self, bint yearfirst, bint dayfirst):
        cdef:
            int ymd_len = len(self._lst)
            int year = -1
            int month = -1
            int day = -1
            dict strids = {}
            str key
            int val
            int mstridx
            int other

        for key, val in (("y", self.ystridx), ("m", self.mstridx), ("d", self.dstridx)):
            if val != -1:
                strids[key] = val

        if (
            len(self._lst) == len(strids) > 0 
            or (len(self._lst) == 3 and len(strids) == 2)
        ):
            return self._resolve_from_stridxs(strids)

        mstridx = self.mstridx

        if ymd_len > 3:
            raise ValueError("More than three YMD values")

        elif ymd_len == 1 or (mstridx != -1 and ymd_len == 2):
            # One member, or two members with a month string
            if mstridx != -1:
                month = self._lst[mstridx]
                # since mstridx is 0 or 1, self._lst[mstridx-1] always
                # looks up the other element
                other = self._lst[mstridx - 1]
            else:
                other = self._lst[0]

            if ymd_len > 1 or mstridx == -1:
                if other > 31:
                    year = other
                else:
                    day = other

        elif ymd_len == 2:
            # Two members with numbers
            if self._lst[0] > 31:
                # 99-01
                year, month = self._lst
            elif self._lst[1] > 31:
                # 01-99
                month, year = self._lst
            elif dayfirst and self._lst[1] <= 12:
                # 13-01
                day, month = self._lst
            else:
                # 01-13
                month, day = self._lst

        elif ymd_len == 3:
            # Three members
            if mstridx == 0:
                if self._lst[1] > 31:
                    # Apr-2003-25
                    month, year, day = self._lst
                else:
                    month, day, year = self._lst
            elif mstridx == 1:
                if self._lst[0] > 31 or (yearfirst and self._lst[2] <= 31):
                    # 99-Jan-01
                    year, month, day = self._lst
                else:
                    # 01-Jan-01
                    # Give precedence to day-first, since
                    # two-digit years is usually hand-written.
                    day, month, year = self._lst

            elif mstridx == 2:
                # WTF!?
                if self._lst[1] > 31:
                    # 01-99-Jan
                    day, year, month = self._lst
                else:
                    # 99-01-Jan
                    year, day, month = self._lst

            else:
                if (
                    self._lst[0] > 31
                    or self.ystridx == 0
                    or (yearfirst and self._lst[1] <= 12 and self._lst[2] <= 31)
                ):
                    # 99-01-01
                    if dayfirst and self._lst[2] <= 12:
                        year, day, month = self._lst
                    else:
                        year, month, day = self._lst
                elif self._lst[0] > 12 or (dayfirst and self._lst[1] <= 12):
                    # 13-01-01
                    day, month, year = self._lst
                else:
                    # 01-13-01
                    month, day, year = self._lst

        return year, month, day

    def __len__(self) -> int:
        return self._lst.__len__()

    def __getitem__(self, key: int) -> int:
        return self._lst.__getitem__(key)

    def __setitem__(self, key: int, value) -> None:
        self._lst.__setitem__(key, value)

    def __delitem__(self, key: int) -> None:
        self._lst.__delitem__(key)

    def __iter__(self):
        return self._lst.__iter__()

    def __contains__(self, item) -> bool:
        return self._lst.__contains__(item)

    def __repr__(self) -> str:
        return self._lst.__repr__()

# praser --------------------------------------------------------------------------------
cdef class parser:
    cdef:
        parserinfo info

    def __init__(self):
        self.info: parserinfo = parserinfo()

    cpdef parse(
        self,
        str timestr,
        bint common_fmts,
        object default,
        bint ignoretz,
        dict tzinfos,
        bint dayfirst,
        bint yearfirst,
        bint fuzzy,
    ):
        """Parse the date/time string into a :class:`datetime.datetime` object.

        :param timestr:
            Any date/time string using the supported formats.

        :param common_fmts:
            Try parsing with common formats. If hitted, can greatly improve
            performance. However, when missed, will introduce slight (20%)
            overhead to the overall parsing time.
            - Common formats:
            "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", 
            "%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d", 
            "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", 
            "%H:%M:%S.%f", "%H:%M:%S", 

        :param default:
            The default datetime object, if this is a datetime object and not
            ``None``, elements specified in ``timestr`` replace elements in the
            default object.

        :param ignoretz:
            If set ``True``, time zones in parsed strings are ignored and a
            naive :class:`datetime.datetime` object is returned.

        :param tzinfos:
            Additional time zone names / aliases which may be present in the
            string. This argument maps time zone names (and optionally offsets
            from those time zones) to time zones. This parameter can be a
            dictionary with timezone aliases mapping time zone names to time
            zones or a function taking two parameters (``tzname`` and
            ``tzoffset``) and returning a time zone.

            The timezones to which the names are mapped can be an integer
            offset from UTC in seconds or a :class:`tzinfo` object.

            .. doctest::
               :options: +NORMALIZE_WHITESPACE

            >>> from dateutil.parser import parse
                from dateutil.tz import gettz
                tzinfos = {"BRST": -7200, "CST": gettz("America/Chicago")}
                parse("2012-01-19 17:21:00 BRST", tzinfos=tzinfos)
                datetime.datetime(2012, 1, 19, 17, 21, tzinfo=tzoffset(u'BRST', -7200))
                parse("2012-01-19 17:21:00 CST", tzinfos=tzinfos)
                datetime.datetime(2012, 1, 19, 17, 21, tzinfo=tzfile('/usr/share/zoneinfo/America/Chicago'))

            This parameter is ignored if ``ignoretz`` is set.

        :param dayfirst:
            Whether to interpret the first value in an ambiguous 3-integer date
            (e.g. 01/05/09) as the day (``True``) or month (``False``). If
            ``yearfirst`` is set to ``True``, this distinguishes between YDM
            and YMD. Defaults to ``False``.

        :param yearfirst:
            Whether to interpret the first value in an ambiguous 3-integer date
            (e.g. 01/05/09) as the year. If ``True``, the first number is taken
            to be the year, otherwise the last number is taken to be the year.
            Defaults to ``False``.

        :param fuzzy:
            Whether to allow fuzzy parsing, allowing for string like "Today is
            January 1, 2047 at 8:21:00AM".

        :return:
            Returns a :class:`datetime.datetime` object.

        :raises ValueError:
            Raised for invalid or unknown string format, if the provided
            :class:`tzinfo` is not in a valid format, or if an invalid date
            would be created.

        :raises TypeError:
            Raised for non-string or character stream input.

        :raises OverflowError:
            Raised if the parsed date exceeds the largest valid C integer on
            your system.
        """

        cdef:
            dtresult res
            str msg

        # Try parsing commom formats
        if common_fmts:
            ret = parse_common(timestr)
            if ret is not None:
                return ret

        # Hard parsing
        if default is None:
            default = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            res = self._parse(timestr, dayfirst, yearfirst, fuzzy)
        except Exception as err:
            msg = str(err)
            if timestr not in msg:
                msg = f"{timestr} - {msg}"
            raise ValueError("Can't parse string: %s" % msg) from err

        try:
            ret = self._build_naive(res, default)
        except ValueError as err:
            raise ValueError(str(err) + ": %s", timestr)

        if not ignoretz:
            return self._build_tzaware(ret, res, tzinfos)
        else:
            return ret

    cpdef _parse(
        self,
        str timestr,
        bint dayfirst,
        bint yearfirst,
        bint fuzzy,
    ):
        """Private method which performs the heavy lifting of parsing, called from
        ``parse()``, which passes on its ``kwargs`` to this function.

        :param timestr:
            The string to parse.

        :param dayfirst:
            Whether to interpret the first value in an ambiguous 3-integer date
            (e.g. 01/05/09) as the day (``True``) or month (``False``). If
            ``yearfirst`` is set to ``True``, this distinguishes between YDM
            and YMD. If set to ``None``, this value is retrieved from the
            current :class:`parserinfo` object (which itself defaults to
            ``False``).

        :param yearfirst:
            Whether to interpret the first value in an ambiguous 3-integer date
            (e.g. 01/05/09) as the year. If ``True``, the first number is taken
            to be the year, otherwise the last number is taken to be the year.
            If this is set to ``None``, the value is retrieved from the current
            :class:`parserinfo` object (which itself defaults to ``False``).

        :param fuzzy:
            Whether to allow fuzzy parsing, allowing for string like "Today is
            January 1, 2047 at 8:21:00AM".
        """

        cdef:
            parserinfo info = self.info
            dtresult res = dtresult()
            list skipped_idxs = []
            YMD ymd = YMD()
            list tokens = timelex.split(timestr)
            int token_len = len(tokens)
            int idx = 0
            str value_repr
            int value
            bint is_number
            str sep
            int signal
            int value_len
            int hour_offset
            int min_offset
            int year
            int month
            int day

        while idx < token_len:
            # Check if it's a number
            value_repr = tokens[idx]
            try:
                float(value_repr)
            except ValueError:
                is_number = False
            else:
                is_number = True

            if is_number:
                # Numeric token
                idx = self._parse_numeric_token(tokens, idx, info, ymd, res, fuzzy)
                idx += 1
                continue

            # Check weekday
            value = info.weekday(tokens[idx])
            if value != -1:
                res.set_weekday(value)
                idx += 1
                continue

            # Check month name
            value = info.month(tokens[idx])
            if value != -1:
                ymd.append(value, "M")
                if idx + 1 < token_len:
                    if tokens[idx + 1] in ("-", "/"):
                        # Jan-01[-99]
                        sep = tokens[idx + 1]
                        ymd.append(tokens[idx + 2])
                        if idx + 3 < token_len and tokens[idx + 3] == sep:
                            # Jan-01-99
                            ymd.append(tokens[idx + 4])
                            idx += 2
                        idx += 2

                    elif (
                        idx + 4 < token_len
                        and tokens[idx + 1] == tokens[idx + 3] == " "
                        and info.pertain(tokens[idx + 2])
                    ):
                        # Jan of 01
                        # In this case, 01 is clearly year
                        if tokens[idx + 4].isdigit():
                            # Convert it here to become unambiguous
                            value = int(tokens[idx + 4])
                            ymd.append(str(info.convertyear(value)), "Y")
                        else:
                            # Wrong guess
                            pass
                            # TODO: not hit in tests
                        idx += 4
                idx += 1
                continue

            # Check am/pm
            value = info.ampm(tokens[idx])
            if value != -1:
                if self._ampm_valid(res.hour, res.ampm, fuzzy):
                    res.set_hour(self._adjust_ampm(res.hour, value))
                    res.set_ampm(value)
                elif fuzzy:
                    skipped_idxs.append(idx)
                idx += 1
                continue

            # Check for a timezone name
            if self._could_be_tzname(
                res.hour, res.tzname, res.tzoffset, tokens[idx]
            ):
                res.set_tzname(tokens[idx])
                res.set_tzoffset(info.tzoffset(res.tzname))

                # Check for something like GMT+3, or BRST+3. Notice
                # that it doesn't mean "I am 3 hours after GMT", but
                # "my time +3 is GMT". If found, we reverse the
                # logic so that timezone parsing code will get it
                # right.
                if idx + 1 < token_len and tokens[idx + 1] in ("+", "-"):
                    tokens[idx + 1] = ("+", "-")[tokens[idx + 1] == "+"]
                    res.set_tzoffset(-999999)
                    if info.utczone(res.tzname):
                        # With something like GMT+3, the timezone
                        # is *not* GMT.
                        res.set_tzname("")

            # Check for a numbered timezone
            elif res.hour != -1 and tokens[idx] in ("+", "-"):
                signal = (-1, 1)[tokens[idx] == "+"]
                value_len = len(tokens[idx + 1])

                # TODO: check that tokens[idx + 1] is integer?
                if value_len == 4:
                    # -0300
                    hour_offset = int(tokens[idx + 1][:2])
                    min_offset = int(tokens[idx + 1][2:])
                elif idx + 2 < token_len and tokens[idx + 2] == ":":
                    # -03:00
                    hour_offset = int(tokens[idx + 1])
                    # TODO: Check that tokens[idx+3] is minute-like?
                    min_offset = int(tokens[idx + 3])  
                    idx += 2
                elif value_len <= 2:
                    # -[0]3
                    hour_offset = int(tokens[idx + 1][:2])
                    min_offset = 0
                else:
                    raise ValueError(timestr)

                res.set_tzoffset(signal * (hour_offset * 3600 + min_offset * 60))

                # Look for a timezone name between parenthesis
                if (
                    idx + 5 < token_len
                    and info.jump(tokens[idx + 2])
                    and tokens[idx + 3] == "("
                    and tokens[idx + 5] == ")"
                    and 3 <= len(tokens[idx + 4])
                    and self._could_be_tzname(
                        res.hour, res.tzname, -999999, tokens[idx + 4]
                    )
                ):
                    # -0300 (BRST)
                    res.set_tzname(tokens[idx + 4])
                    idx += 4
                idx += 1

            # Check jumps
            elif not (info.jump(tokens[idx]) or fuzzy):
                raise ValueError(timestr)
            else:
                skipped_idxs.append(idx)
            idx += 1

        # Process year/month/day
        year, month, day = ymd.resolve_ymd(yearfirst, dayfirst)

        res.set_century_specified(ymd.century_specified)
        res.set_year(year)
        res.set_month(month)
        res.set_day(day)

        if info.validate(res):
            return res
        else:
            raise ValueError("Invalid res: %s" % res)

    cpdef int _parse_numeric_token(
        self,
        list tokens,
        int idx,
        parserinfo info,
        YMD ymd,
        dtresult res,
        bint fuzzy,
    ):
        # Token is a number
        cdef:
            int token_len = len(tokens)
            str value_repr = tokens[idx]
            int value_len = len(value_repr)
            int hms_idx
            int hms
            int hour
            int minute
            int second
            int microsecond
            str sep

        try:
            value = self._to_decimal(value_repr)
        except Exception as err:
            raise ValueError("Unknown numeric token: %s" % err)

        if (
            len(ymd) == 3
            and value_len in (2, 4)
            and res.hour == -1
            and (
                idx + 1 >= token_len
                or (tokens[idx + 1] != ":" and info.hms(tokens[idx + 1]) == -1)
            )
        ):
            # 19990101T23[59]
            res.set_hour(int(value_repr[:2]))

            if value_len == 4:
                res.set_minute(int(value_repr[2:]))
            return idx

        if value_len == 6 or (value_len > 6 and value_repr.find(".") == 6):
            # YYMMDD or HHMMSS[.ss]
            if not ymd and "." not in value_repr:
                ymd.append(value_repr[:2])
                ymd.append(value_repr[2:4])
                ymd.append(value_repr[4:])
            else:
                # 19990101T235959[.59]

                # TODO: Check if res attributes already set.
                res.set_hour(int(value_repr[:2]))
                res.set_minute(int(value_repr[2:4]))
                second, microsecond = self._parsems(value_repr[4:])
                res.set_second(second)
                res.set_microsecond(microsecond)
            return idx

        if value_len in (8, 12, 14):
            # YYYYMMDD
            ymd.append(value_repr[:4], "Y")
            ymd.append(value_repr[4:6])
            ymd.append(value_repr[6:8])

            if value_len > 8:
                res.set_hour(int(value_repr[8:10]))
                res.set_minute(int(value_repr[10:12]))

                if value_len > 12:
                    res.set_second(int(value_repr[12:]))
            return idx

        hms_idx = self._find_hms_idx(idx, tokens, info, True)
        if hms_idx != -1:
            # HH[ ]h or MM[ ]m or SS[.ss][ ]s
            idx, hms = self._parse_hms(idx, tokens, info, hms_idx)
            if hms != -1:
                # TODO: checking that hour/minute/second are not
                # already set?
                self._assign_hms(res, value_repr, hms)
            return idx

        if idx + 2 < token_len and tokens[idx + 1] == ":":
            # HH:MM[:SS[.ss]]
            res.set_hour(int(value))
            value = self._to_decimal(tokens[idx + 2])  # TODO: try/except for this?
            minute, second = self._parse_min_sec(value)
            res.set_minute(minute)
            res.set_second(second)

            if idx + 4 < token_len and tokens[idx + 3] == ":":
                second, microsecond = self._parsems(tokens[idx + 4])
                res.set_second(second)
                res.set_microsecond(microsecond)
                idx += 2
            idx += 2
            return idx

        if idx + 1 < token_len and tokens[idx + 1] in ("-", "/", "."):
            sep = tokens[idx + 1]
            ymd.append(value_repr)

            if idx + 2 < token_len and not info.jump(tokens[idx + 2]):
                if tokens[idx + 2].isdigit():
                    # 01-01[-01]
                    ymd.append(tokens[idx + 2])
                else:
                    # 01-Jan[-01]
                    value = info.month(tokens[idx + 2])

                    if value != -1:
                        ymd.append(value, "M")
                    else:
                        raise ValueError()

                if idx + 3 < token_len and tokens[idx + 3] == sep:
                    # We have three members
                    value = info.month(tokens[idx + 4])

                    if value != -1:
                        ymd.append(value, "M")
                    else:
                        ymd.append(tokens[idx + 4])
                    idx += 2

                idx += 1
            idx += 1
            return idx

        if idx + 1 >= token_len or info.jump(tokens[idx + 1]):
            if idx + 2 < token_len and info.ampm(tokens[idx + 2]) != -1:
                # 12 am
                hour = int(value)
                res.set_hour(self._adjust_ampm(hour, info.ampm(tokens[idx + 2])))
                idx += 1
            else:
                # Year, month or day
                ymd.append(value)
            idx += 1
            return idx

        if info.ampm(tokens[idx + 1]) != -1 and (0 <= value < 24):
            # 12am
            hour = int(value)
            res.set_hour(self._adjust_ampm(hour, info.ampm(tokens[idx + 1])))
            idx += 1
            return idx

        if ymd.could_be_day(value):
            ymd.append(value)
            return idx

        elif not fuzzy:
            raise ValueError()

        else:
            return idx

    cpdef int _find_hms_idx(
        self, 
        int idx, 
        list tokens, 
        parserinfo info,
        bint allow_jump,
    ):
        cdef:
            int token_len = len(tokens)
            int hms_idx

        if idx + 1 < token_len and info.hms(tokens[idx + 1]) != -1:
            # There is an "h", "m", or "s" label following this token.  We take
            # assign the upcoming label to the current token.
            # e.g. the "12" in 12h"
            hms_idx = idx + 1

        elif (
            allow_jump
            and idx + 2 < token_len
            and tokens[idx + 1] == " "
            and info.hms(tokens[idx + 2]) != -1
        ):
            # There is a space and then an "h", "m", or "s" label.
            # e.g. the "12" in "12 h"
            hms_idx = idx + 2

        elif idx > 0 and info.hms(tokens[idx - 1]) != -1:
            # There is a "h", "m", or "s" preceding this token.  Since neither
            # of the previous cases was hit, there is no label following this
            # token, so we use the previous label.
            # e.g. the "04" in "12h04"
            hms_idx = idx - 1

        elif (
            1 < idx == token_len - 1
            and tokens[idx - 1] == " "
            and info.hms(tokens[idx - 2]) != -1
        ):
            # If we are looking at the final token, we allow for a
            # backward-looking check to skip over a space.
            # TODO: Are we sure this is the right condition here?
            hms_idx = idx - 2

        else:
            hms_idx = -1

        return hms_idx

    cpdef bint _assign_hms(self, dtresult res, str value_repr, int hms):
        # See GH issue #427, fixing float rounding
        cdef:
            int minute
            int second
            int microsecond

        value = self._to_decimal(value_repr)
        if hms == 0:
            # Hour
            res.set_hour(int(value))
            remainder = value % 1
            if remainder:
                res.set_minute(int(60 * remainder))

        elif hms == 1:
            minute, second = self._parse_min_sec(value)
            res.set_minute(minute)
            res.set_second(second)

        elif hms == 2:
            second, microsecond = self._parsems(value_repr)
            res.set_second(second)
            res.set_microsecond(microsecond)

        return True

    cpdef bint _could_be_tzname(self, int hour, str tzname, int tzoffset, str token):
        return (
            hour != -1
            and not tzname
            and tzoffset == -999999
            and len(token) <= 5
            and (all([x in ascii_uppercase for x in token]) or self.info.utczone(token))
        )

    cpdef bint _ampm_valid(self, int hour, int ampm, bint fuzzy):
        """For fuzzy parsing, 'a' or 'am' (both valid English words)
        may erroneously trigger the AM/PM flag. Deal with that
        here.
        """

        cdef:
            bint val_is_ampm = True

        # If there's already an AM/PM flag, this one isn't one.
        if fuzzy and ampm != -1:
            val_is_ampm = False

        # If AM/PM is found and hour is not, raise a ValueError
        if hour == -1:
            if fuzzy:
                val_is_ampm = False
            else:
                raise ValueError("No hour specified with AM or PM flag.")

        elif not 0 <= hour <= 12:
            # If AM/PM is found, it's a 12 hour clock, so raise
            # an error for invalid range
            if fuzzy:
                val_is_ampm = False
            else:
                raise ValueError("Invalid hour specified for 12-hour clock.")

        return val_is_ampm

    cdef int _adjust_ampm(self, int hour, int ampm):
        if 0 < hour < 12 and ampm == 1:
            hour += 12
        elif hour == 12 and ampm == 0:
            hour = 0
        return hour

    cpdef _parse_min_sec(self, value):
        # TODO: Every usage of this function sets res.second to the return
        # value. Are there any cases where second will be returned as None and
        # we *don't* want to set res.second = None?
        cdef:
            int minute = int(value)
            int second = -1

        remainder = value % 1
        if remainder:
            second = int(60 * remainder)
        return minute, second

    cpdef _parse_hms(self, int idx, list tokens, parserinfo info, int hms_idx):
        # TODO: Is this going to admit a lot of false-positives for when we
        # just happen to have digits and "h", "m" or "s" characters in non-date
        # text?  I guess hex hashes won't have that problem, but there's plenty
        # of random junk out there.
        cdef:
            int hms
            int new_idx

        if hms_idx == -1:
            hms = -1
            new_idx = idx
        elif hms_idx > idx:
            hms = info.hms(tokens[hms_idx])
            new_idx = hms_idx
        else:
            # Looking backwards, increment one.
            hms = info.hms(tokens[hms_idx]) + 1
            new_idx = idx

        return new_idx, hms

    # ------------------------------------------------------------------
    # Handling for individual tokens.  These are kept as methods instead
    #  of functions for the sake of customizability via subclassing.
    cpdef _parsems(self, str value):
        """Parse a I[.F] seconds value into (seconds, microseconds)."""

        cdef:
            int second
            int microsecond = 0

        if "." not in value:
            second = int(value)
            return second, microsecond
        else:
            sec, mms = value.split(".")
            second = int(sec)
            microsecond = int(mms.ljust(6, "0")[:6])
            return second, microsecond

    def _to_decimal(self, val):
        try:
            decimal_value = Decimal(str(val))
            # See GH 662, edge case, infinite value should not be converted
            #  via `_to_decimal`
            if not decimal_value.is_finite():
                raise ValueError("Converted decimal value is infinite or NaN")
        except Exception as err:
            raise ValueError("Could not convert %s to decimal: %s" % val, err)
        else:
            return decimal_value

    # ------------------------------------------------------------------
    # Post-Parsing construction of datetime output.  These are kept as
    #  methods instead of functions for the sake of customizability via
    #  subclassing.
    def _build_tzinfo(self, tzinfos: dict[str, int], tzname: str, tzoffset: int):
        if callable(tzinfos):
            tzdata = tzinfos(tzname, tzoffset)
        else:
            tzdata = tzinfos.get(tzname)
        # handle case where tzinfo is paased an options that returns None
        # eg tzinfos = {'BRST' : None}
        if isinstance(tzdata, dt_tzinfo) or tzdata is None:
            tzinfo = tzdata
        elif isinstance(tzdata, text_type):
            tzinfo = _tz.tzstr(tzdata)
        elif isinstance(tzdata, integer_types):
            tzinfo = _tz.tzoffset(tzname, tzdata)
        else:
            raise TypeError(
                "Offset must be tzinfo subclass, tz string, " "or int offset."
            )
        return tzinfo

    def _build_tzaware(self, naive: datetime, res: dtresult, tzinfos: dict[str, int]):
        if callable(tzinfos) or (tzinfos and res.tzname in tzinfos):
            tzinfo = self._build_tzinfo(tzinfos, res.tzname, res.tzoffset)
            aware = naive.replace(tzinfo=tzinfo)
            aware = self._assign_tzname(aware, res.tzname)

        elif res.tzname and res.tzname in t_tzname:
            aware = naive.replace(tzinfo=_tz.tzlocal())

            # Handle ambiguous local datetime
            aware = self._assign_tzname(aware, res.tzname)

            # This is mostly relevant for winter GMT zones parsed in the UK
            if aware.tzname() != res.tzname and self.info.utczone(res.tzname):
                aware = aware.replace(tzinfo=_tz.UTC)

        elif res.tzoffset == 0:
            aware = naive.replace(tzinfo=_tz.UTC)

        elif res.tzoffset != -999999:
            aware = naive.replace(tzinfo=_tz.tzoffset(res.tzname, res.tzoffset))

        elif not res.tzname and res.tzoffset == -999999:
            # i.e. no timezone information was found.
            aware = naive

        elif res.tzname:
            aware = naive

        return aware

    cpdef _build_naive(self, dtresult res, object default):
        cdef:
            dict repl = {}
            str key
            int cyear
            int cmonth
            int cday
            object native

        for key, val in res.values.items():
            if key in ("year", "month", "day", "hour", "minute", "second", "microsecond"):
                repl[key] = val

        if "day" not in repl:
            # If the default day exceeds the last day of the month, fall back
            # to the end of the month.
            cyear = default.year if res.year == -1 else res.year
            cmonth = default.month if res.month == -1 else res.month
            cday = default.day if res.day == -1 else res.day

            if cday > monthrange(cyear, cmonth)[1]:
                repl["day"] = monthrange(cyear, cmonth)[1]

        naive = default.replace(**repl)

        if res.weekday != -1 and res.day == -1:
            naive = naive + ctimedelta(weekday=res.weekday)

        return naive

    def _assign_tzname(self, dt: datetime, tzname: str):
        if dt.tzname() != tzname:
            new_dt = _tz.enfold(dt, fold=1)
            if new_dt.tzname() == tzname:
                return new_dt
        return dt

# ---------------------------------------------------------------------------------------
cdef str _FMT_ISO_MMS = "%Y-%m-%dT%H:%M:%S.%f"
cdef str _FMT_ISO = "%Y-%m-%dT%H:%M:%S"
cdef str _FMT_DASH_DT_MMS = "%Y-%m-%d %H:%M:%S.%f"
cdef str _FMT_DASH_DT = "%Y-%m-%d %H:%M:%S"
cdef str _FMT_DASH_DATE = "%Y-%m-%d"
cdef str _FMT_SLASH_DT_MMS = "%Y/%m/%d %H:%M:%S.%f"
cdef str _FMT_SLASH_DT = "%Y/%m/%d %H:%M:%S"
cdef str _FMT_SLASH_DATE = "%Y/%m/%d"
cdef str _FMT_TIME_MMS = "%H:%M:%S.%f"
cdef str _FMT_TIME = "%H:%M:%S"

cpdef parse_common(str val):
    try:
        # ISO
        if "T" in val:
            if "." in val:
                try:
                    return datetime.strptime(val, _FMT_ISO_MMS)
                except ValueError:
                    pass
            else:
                try:
                    return datetime.strptime(val, _FMT_ISO)
                except ValueError:
                    pass

        # Dash
        elif "-" in val:
            if "." in val:
                try:
                    return datetime.strptime(val, _FMT_DASH_DT_MMS)
                except ValueError:
                    pass
            elif ":" in val:
                try:
                    return datetime.strptime(val, _FMT_DASH_DT)
                except ValueError:
                    pass
            else:
                try:
                    return datetime.strptime(val, _FMT_DASH_DATE)
                except ValueError:
                    pass

        # Slash
        elif "/" in val:
            if "." in val:
                try:
                    return datetime.strptime(val, _FMT_SLASH_DT_MMS)
                except ValueError:
                    pass
            elif ":" in val:
                try:
                    return datetime.strptime(val, _FMT_SLASH_DT)
                except ValueError:
                    pass
            else:
                try:
                    return datetime.strptime(val, _FMT_SLASH_DATE)
                except ValueError:
                    pass

        # Time
        elif ":" in val:
            if "." in val:
                try:
                    return datetime.strptime(val, _FMT_TIME_MMS)
                except ValueError:
                    pass
            else:
                try:
                    return datetime.strptime(val, _FMT_TIME)
                except ValueError:
                    pass

        # No match
        return None

    except Exception:
        return None

cpdef parse_exacts(str val, tuple fmts):
    cdef str fmt

    for fmt in fmts:
        try:
            return datetime.strptime(val, fmt)
        except Exception:
            pass

    return None







