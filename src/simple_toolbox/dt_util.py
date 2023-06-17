#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from warnings import warn as _warn
from re import compile as _re_compile
from typing import Any, Callable, Self
from calendar import monthrange as _monthrange
from datetime import date as _dt_date, time as _dt_time
from datetime import datetime as _datetime, timedelta as _timedelta

from numpy import datetime64 as _datetime64
from pandas.tseries import offsets as _offsets
from pandas import to_datetime as _pd_to_datetime
from pandas import TimedeltaIndex as _TimedeltaIndex
from pandas import Series as _Series, Timestamp as _Timestamp

from simple_toolbox.cython_core.dt_parser_c import parser as _dt_parser
from simple_toolbox.cython_core.dt_parser_c import ctimedelta as ctimedelta_c
from simple_toolbox.cython_core.dt_parser_c import parse_common as _parse_common
from simple_toolbox.cython_core.dt_parser_c import parse_exacts as _parse_exacts
from simple_toolbox.cython_core.dt_util_c import unix_timestamp as _unix_timestamp
from simple_toolbox.cython_core.dt_util_c import seconds_to_time as _seconds_to_time

__all__ = [
    "TimeUtils",
    "Python_Datetime",
    "Pandas_Datetime",
    "parse",
    "parse_common",
    "parse_exact",
    "cal_time_range",
    "gen_range_time",
    "unix_timestamp",
    "seconds_to_time",
    "ctimedelta",
    "ctimedelta_c",
]


# Constant ===================================================================================
class TimeUtils:
    WEEKDAY_MATCH: dict[str, int] = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6,
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
        "Mon": 0,
        "Tue": 1,
        "Wed": 2,
        "Thu": 3,
        "Fri": 4,
        "Sat": 5,
        "Sun": 6,
        "Mon.": 0,
        "Tue.": 1,
        "Wed.": 2,
        "Thu.": 3,
        "Fri.": 4,
        "Sat.": 5,
        "Sun.": 6,
        "mon": 0,
        "tue": 1,
        "wed": 2,
        "thu": 3,
        "fri": 4,
        "sat": 5,
        "sun": 6,
        "mon.": 0,
        "tue.": 1,
        "wed.": 2,
        "thu.": 3,
        "fri.": 4,
        "sat.": 5,
        "sun.": 6,
        1: 0,
        2: 1,
        3: 2,
        4: 3,
        5: 4,
        6: 5,
        7: 6,
    }
    TIME_UNIT_MATCH: dict[str, str] = {
        "Y": "year",
        "Yr": "year",
        "yr": "year",
        "Year": "year",
        "year": "year",
        "M": "month",
        "Mth": "month",
        "mth": "month",
        "Month": "month",
        "month": "month",
        "W": "week",
        "Wk": "week",
        "wk": "week",
        "Week": "week",
        "week": "week",
        "D": "day",
        "Dy": "day",
        "dy": "day",
        "Day": "day",
        "day": "day",
        "h": "hour",
        "Hr": "hour",
        "hr": "hour",
        "Hour": "hour",
        "hour": "hour",
        "m": "minute",
        "Min": "minute",
        "min": "minute",
        "Minute": "minute",
        "minute": "minute",
        "s": "second",
        "Sec": "second",
        "sec": "second",
        "Second": "second",
        "second": "second",
    }
    EXTRA_DATETIME_FORMATS: tuple[str] = ("%d%m%Y",)
    CN_DATE_RE = _re_compile(
        r"(\d{4}年)(\d{1,2}月)?(\d{1,2}日)?[ ]?(\d{1,2}[小时])?(\d{1,2}[分钟])?(\d{1,2}秒)?"
    )
    DEFAULT_DATETIME: _datetime = _datetime(1970, 1, 1, 0, 0, 0)
    DEFAULT_DATE: _dt_date = _dt_date(1970, 1, 1)
    DEFAULT_TIME: _dt_time = _dt_time(0, 0, 0)


# Classes ====================================================================================
class Python_Datetime:
    """A simple Class to parse most python `datetime` related objects into `datetime`,
    and provide some useful properties & functions to manipulate the it.

    :param __o: The object to be parsed into `datetime`.
        - If not provided, will default to `datetime.now`.

    :param formats: The string formats to be used to parse the object into `datetime`.
        - Use it when the format of the object is known to increase performance.
        - If not provided, the default formats will be used, which can handle most cases.

    :param common_fmts: Try parsing with common formats first - `default`: `True`.
        - If hitted, can greatly improve performance. However, missed formats
          will introduce a slight (20%) overhead to the overall parsing time.
        - Common formats:
        - "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
        - "%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d",
        - "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
        - "%H:%M:%S.%f", "%H:%M:%S"

    :param dayfirst: - `default`: `False`
        - Whether to interpret the first value in an ambiguous 3-integer date
          (e.g. 01/05/09) as the day (`True`) or month (`False`).
        - If `yearfirst` is set to `True`, this distinguishes between YDM and YMD.
        - * Notice: if custom formats are provided, this parameter will be ignored.

    :param yearfirst: - `default`: `False`
        - Whether to interpret the first value in an ambiguous 3-integer date
          (e.g. 01/05/09) as the year.
        - If `True`, the first number is taken to be the year, otherwise the
          last number is taken to be the year.
        - * Notice: if custom formats are provided, this parameter will be ignored.
    """

    def __init__(
        self,
        __o: object = None,
        *formats: str,
        common_fmts: bool = True,
        dayfirst: bool = False,
        yearfirst: bool = False,
    ) -> None:
        self.__formats: tuple[str] = formats
        self.__common_fmts: bool = common_fmts
        self.__dayfirst: bool = dayfirst
        self.__yearfirst: bool = yearfirst
        if __o is None:
            self.__dt_obj = _datetime.now()
        else:
            self.__dt_obj = self.__to_datetime(
                __o,
                *self.__formats,
                common_fmts=self.__common_fmts,
                dayfirst=self.__dayfirst,
                yearfirst=self.__yearfirst,
            )

    @property
    def dt(self) -> _datetime:
        return self.__dt_obj

    @property
    def dtStr(self) -> str:
        return str(self.dt)

    @property
    def date(self) -> _dt_date:
        return self.dt.date()

    @property
    def dateStr(self) -> str:
        return str(self.date)

    @property
    def time(self) -> _dt_time:
        return self.dt.time()

    @property
    def timeStr(self) -> str:
        return str(self.time)

    @property
    def timestamp(self) -> _Timestamp:
        return _Timestamp(self.dt)

    @property
    def yesterday(self) -> _datetime:
        return self.dt + _timedelta(days=-1)

    @property
    def tomorrow(self) -> _datetime:
        return self.dt + _timedelta(days=1)

    @property
    def monday(self) -> _datetime:
        return self.dt + _timedelta(days=-self.dt.weekday())

    @property
    def tuesday(self) -> _datetime:
        return self.dt + _timedelta(days=-self.dt.weekday() + 1)

    @property
    def wednesday(self) -> _datetime:
        return self.dt + _timedelta(days=-self.dt.weekday() + 2)

    @property
    def thursday(self) -> _datetime:
        return self.dt + _timedelta(days=-self.dt.weekday() + 3)

    @property
    def friday(self) -> _datetime:
        return self.dt + _timedelta(days=-self.dt.weekday() + 4)

    @property
    def saturday(self) -> _datetime:
        return self.dt + _timedelta(days=-self.dt.weekday() + 5)

    @property
    def sunday(self) -> _datetime:
        return self.dt + _timedelta(days=-self.dt.weekday() + 6)

    @property
    def month1stDay(self) -> _datetime:
        return self.dt.replace(day=1)

    @property
    def monthlstDay(self) -> _datetime:
        return self.__month_last_day(self.dt)

    @property
    def monthDays(self) -> int:
        """How many days in the month of the `datetime`."""

        return self.__month_max_days(self.dt)

    def last_week(self, weekday: int | str = None) -> Self:
        """Manipulate the `datetime` to last week.

        :param weekday: The specific weekday to be manipulated to.
            - If not provided, will default to the same weekday in last week
            - For `str` input, accepts: `Monday`, `monday`, `Mon', `Mon.`, `mon`, `mon.` ...
            - For `int` input, starts from `1` for `Monday`, ends at `7` for `Sunday`

        :raises `ValueError`: If the `weekday` input is not supported.
        """

        if weekday is None:
            return self.__new(self.dt + _timedelta(days=-7))

        if weekday not in TimeUtils.WEEKDAY_MATCH:
            raise ValueError(f"<last_week> Unsupported weekday input: {weekday}")

        return self.__new(
            self.dt
            + _timedelta(
                days=(-7 - self.dt.weekday() + TimeUtils.WEEKDAY_MATCH[weekday])
            )
        )

    def next_week(self, weekday: int | str = None) -> Self:
        """Manipulate the `datetime` to next week.

        :param weekday: The specific weekday to be manipulated to.
            - If not provided, will default to the same weekday in next week
            - For `str` input, accepts: `Monday`, `monday`, `Mon', `Mon.`, `mon`, `mon.` ...
            - For `int` input, starts from `1` for `Monday`, ends at `7` for `Sunday`

        :raises `ValueError`: If the `weekday` input is not supported.
        """

        if weekday is None:
            return self.__new(self.dt + _timedelta(days=7))

        if weekday not in TimeUtils.WEEKDAY_MATCH:
            raise ValueError(f"<next_week> Unsupported weekday input: {weekday}")

        return self.__new(
            self.dt
            + _timedelta(days=7 - self.dt.weekday() + TimeUtils.WEEKDAY_MATCH[weekday])
        )

    def curr_week(self, weekday: int | str = None) -> Self:
        """Manipulate the `datetime` to current week.

        :param weekday: The specific weekday to be manipulated to.
            - If not provided, no changes will be made
            - For `str` input, accepts: `Monday`, `monday`, `Mon', `Mon.`, `mon`, `mon.` ...
            - For `int` input, starts from `1` for `Monday`, ends at `7` for `Sunday`

        :raises `ValueError`: If the `weekday` input is not supported.
        """

        if weekday is None:
            return self

        if weekday not in TimeUtils.WEEKDAY_MATCH:
            raise ValueError(f"<curr_week> Unsupported weekday input: {weekday}")

        return self.__new(
            self.dt
            + _timedelta(days=-self.dt.weekday() + TimeUtils.WEEKDAY_MATCH[weekday]),
        )

    def is_weekday(self, weekday: int | str) -> bool:
        """Check if the `datetime` is a specific weekday.

        :param weekday: The specific weekday to be checked.
            - For `str` input, accepts: `Monday`, `monday`, `Mon', `Mon.`, `mon`, `mon.` ...
            - For `int` input, starts from `1` for `Monday`, ends at `7` for `Sunday`

        :raises `ValueError`: If the `weekday` input is not supported.
        :returns: `True` if the `datetime` is the specific weekday, `False` otherwise.
        """

        if weekday not in TimeUtils.WEEKDAY_MATCH:
            raise ValueError(f"<is_weekday> Unsupported weekday input: {weekday}")

        return self.dt.weekday() == TimeUtils.WEEKDAY_MATCH[weekday]

    def last_month(self, day: int = None) -> Self:
        """Manipulate the `datetime` to last month.

        :param day: The specific day to be manipulated to.
            - If not provided, will default to the same day in last month
            - For `day` < `0`, will default to the last day of last month
            - For `day` input exceeds the max days in last month, will also default
              to the last day of last month
        """

        return self.__new(self.__to_day(self.dt + ctimedelta_c(months=-1), day=day))

    def next_month(self, day: int = None) -> Self:
        """Manipulate the `datetime` to next month.

        :param day: The specific day to be manipulated to.
            - If not provided, will default to the same day in next month
            - For `day` < `0`, will default to the last day of next month
            - For `day` input exceeds the max days in next month, will also default
              to the last day of next month
        """

        return self.__new(self.__to_day(self.dt + ctimedelta_c(months=1), day=day))

    def curr_month(self, day: int = None) -> Self:
        """Manipulate the `datetime` to current month.

        :param day: The specific day to be manipulated to.
            - If not provided, no changes will be made
            - For `day` < `0`, will default to the last day of current month
            - For `day` input exceeds the max days in current month, will also default
              to the last day of current month
        """

        return self.__new(self.__to_day(self.dt, day=day))

    def to_month(self, month: int = None, day: int = None) -> Self:
        """Manipulate the `datetime` to specific month and day.

        :param month: The specific month to be manipulated to.
            - If not provided, month will not be changed
            - For `month` < `0` or `month` >= 12, will default to December

        :param day: The specific day to be manipulated to.
            - If not provided, day will not be changed
            - For `day` < `0`, will default to the last day of the specific month
            - For `day` input exceeds the max days in the specific month, will also default
              to the last day of the specific month
        """

        return self.__new(self.__to_day(self.__to_month(self.dt, month=month), day=day))

    def is_monthday(self, day: int) -> bool:
        """Check if the `datetime` is the specific day in month.

        :param day: The specific day to be checked.
            - For `day` < `0`, will default to check if it is the last day of month
            - For `day` input exceeds the max days in the specific month, will also default
              to check if it is the last day of the specific month
        """

        return self.dt.day == self.__to_day(self.dt, day=day).day

    def adjust(
        self,
        *,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
        leapdays: int = 0,
    ) -> Self:
        """Adjust the `datetime` with the specific date & time difference.

        Notice `ONLY` accept integer, and can be negative (argument is plural);

        :param years: number of years to be adjusted - `default`: `0`.
        :param months: number of months to be adjusted - `default`: `0`.
        :param weeks: number of weeks to be adjusted - `default`: `0`.
        :param days: number of days to be adjusted - `default`: `0`.
        :param hours: number of hours to be adjusted - `default`: `0`.
        :param minutes: number of minutes to be adjusted - `default`: `0`.
        :param seconds: number of seconds to be adjusted - `default`: `0`.
        :param microseconds: number of microseconds to be adjusted - `default`: `0`.
        :param leapdays: number of leapdays to be adjusted - `default`: `0`.
        """

        # Perform adjustment
        return self.__new(
            self.dt
            + ctimedelta_c(
                years=years,
                months=months,
                weeks=weeks,
                days=days,
                leapdays=leapdays,
                hours=hours,
                minutes=minutes,
                seconds=seconds,
                microseconds=microseconds,
            )
        )

    def replace(
        self,
        *,
        year: int = None,
        month: int = None,
        day: int = None,
        hour: int = None,
        minute: int = None,
        second: int = None,
        microsecond: int = None,
    ) -> Self:
        """Replace the `datetime` with the specific date & times.

        :param year: The specific year to be replaced.
            - If not provided, year will not be changed

        :param month: The specific month to be replaced.
            - If not provided, month will not be changed
            - For `month` < `0` or `month` > 12, will default to December

        :param day: The specific day to be replaced.
            - If not provided, day will not be changed
            - For `day` < `0`, will default to the last day of the specific month
            - For `day` input exceeds the max days in the specific month, will also default
              to the last day of the specific month

        :param hour: The specific hour to be replaced.
            - If not provided, hour will not be changed
            - For `hour` < `0` or `hour` > 23, will default to 23

        :param minute: The specific minute to be replaced.
            - If not provided, minute will not be changed
            - For `minute` < `0` or `minute` > 59, will default to 59

        :param second: The specific second to be replaced.
            - If not provided, second will not be changed
            - For `second` < `0` or `second` > 59, will default to 59

        :param microsecond: The specific microsecond to be replaced.
            - If not provided, microsecond will not be changed
            - For `microsecond` < `0` or `microsecond` > 999999, will default to 999999
        """

        # no replacement
        if not any([day, month, year, hour, minute, second]):
            return self

        # datetime savepoint
        dt = self.dt

        # year replacement
        year = year or dt.year

        # month replacement
        month = dt.month if not month else month if 0 < month < 12 else 12

        # day replacement
        if not day:
            day = dt.day
        elif 0 < day <= 28:
            pass
        elif 28 < day < 31:
            day = min(day, self.__month_max_days(dt))
        else:
            day = self.__month_max_days(dt)

        # hour replacement
        hour = dt.hour if not hour else hour if 0 < hour < 23 else 23

        # minute replacement
        minute = dt.minute if not minute else minute if 0 < minute < 59 else 59

        # second replacement
        second = dt.second if not second else second if 0 < second < 59 else 59

        # microsecond replacement
        microsecond = (
            dt.microsecond
            if not microsecond
            else microsecond
            if 0 < microsecond < 999999
            else 999999
        )

        # perform replacement
        return self.__new(
            self.dt.replace(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                second=second,
                microsecond=microsecond,
            ),
        )

    def delta(
        self,
        dt: _datetime,
        unit: str = "D",
        *,
        inclusive: bool = False,
    ) -> int:
        """Calculate the time difference between two `datetime` objects.

        :param dt: The extermal `datetime` object to be compared with.
        :param unit: The time unit to be calculated on.
            - `Year`: 'Y', 'Yr', 'yr', 'Year', 'year'
            - `Month`: 'M', 'Mth', 'mth', 'Month', 'month'
            - `Week`: 'W', 'Wk', 'wk', 'Week', 'week'
            - `Day`: 'D', 'Dy', 'dy', 'Day', 'day'
            - `Hour`: 'h', 'Hr', 'hr', 'Hour', 'hour'
            - `Minute`: 'm', 'Min', 'min', 'Minute', 'minute'
            - `Second`: 's', 'Sec', 'sec', 'Second', 'second'

        :param inclusive: whether to include the last delta in the calculation.
            For example, if `dt1` is 2021-02-01 and `dt2` is 2021-02-28,
            - `inclusive` == `True`: the delta of days will be 28 days
            - `inclusive` == `False`: the delta of days will be 27 days
        """

        # validate time unit
        if not (unit := TimeUtils.TIME_UNIT_MATCH.get(unit)):
            raise ValueError(f"<delta> unsupported time unit: '{unit}'")

        # datetime savepoint
        dt1, dt2 = self.dt, self.__to_datetime(dt)

        # adjust datetime order
        if dt1 < dt2:
            dt1, dt2 = dt2, dt1

        # calculate year delta
        if unit == "year":
            delta = dt1.year - dt2.year

        # calculate month delta
        elif unit == "month":
            delta = (dt1.year - dt2.year) * 12 + (dt1.month - dt2.month)

        # calculate week delta
        elif unit == "week":
            delta = (dt1 - dt2 + _timedelta(dt2.weekday())).days // 7

        # calculate day delta
        elif unit == "day":
            delta = (dt1 - dt2).days

        # calculate hour delta
        elif unit == "hour":
            delta = (dt1 - dt2).seconds // 3600

        # calculate minute delta
        elif unit == "minute":
            delta = (dt1 - dt2).seconds // 60

        # calculate second delta
        elif unit == "second":
            delta = (dt1 - dt2).seconds

        # not supported time unit
        else:
            raise ValueError(f"<delta> unsupported time unit: '{unit}'")

        # return delta
        return delta + 1 if inclusive else delta

    # Core functions
    def __new(self, dt: _datetime) -> Self:
        return self.__class__(
            dt,
            *self.__formats,
            common_fmts=self.__common_fmts,
            dayfirst=self.__dayfirst,
            yearfirst=self.__yearfirst,
        )

    def __to_datetime(
        self,
        dt_obj: object,
        *formats: str,
        common_fmts: bool = True,
        dayfirst: bool = False,
        yearfirst: bool = False,
    ) -> _datetime:
        # . Parse datetime object with custom dateuitl.parser
        def parse_by_dt_parser(dt_obj: str) -> _datetime:
            try:
                try:
                    return parse(
                        dt_obj,
                        common_fmts=common_fmts,
                        default=TimeUtils.DEFAULT_DATETIME,
                        dayfirst=dayfirst,
                        yearfirst=yearfirst,
                    )
                except Exception:
                    return parse(
                        dt_obj,
                        common_fmts=False,
                        default=TimeUtils.DEFAULT_DATETIME,
                        dayfirst=dayfirst,
                        yearfirst=yearfirst,
                        fuzzy=True,
                    )
            except Exception:
                raise ValueError(f"Failed with custom `dt_parser`")

        # . Parse datetime object with string formats
        def parse_by_formats(dt_obj: str, *formats: str) -> _datetime:
            try:
                return parse_exact(dt_obj, *formats)
            except Exception:
                raise ValueError(f"Failed with exact formats: {', '.join(formats)}")

        # . Parse datetime object with chinese regex
        def parse_by_chinese_regex(dt_obj: str) -> _datetime:
            try:
                return parse(
                    TimeUtils.CN_DATE_RE.search(dt_obj)[0],
                    common_fmts=False,
                    default=TimeUtils.DEFAULT_DATETIME,
                    dayfirst=dayfirst,
                    yearfirst=yearfirst,
                    fuzzy=True,
                )
            except Exception:
                raise ValueError(f"Failed with chinese `regex`")

        # . Full parse workflow
        def full_parse_workflow(dt_obj: str, *formats: str) -> _datetime:
            # If specific formats are provided, parse with formats
            if formats:
                try:
                    return parse_by_formats(dt_obj, *formats)
                except Exception as err1:
                    err = ValueError(
                        f"<Python_Datetime> Failed to parse: {repr(dt_obj)} {type(dt_obj)}"
                    )
                    err.add_note(f"-> {err1}")
                    raise err

            # Try to parse datetime object with custom dateutil.parser
            try:
                return parse_by_dt_parser(dt_obj)
            except Exception as err1:
                err = ValueError(
                    f"<Python_Datetime> Failed to parse: {repr(dt_obj)} {type(dt_obj)}"
                )
                err.add_note(f"-> {err1}")

            # Try to parse datetime object with string formats
            try:
                return parse_by_formats(dt_obj, *TimeUtils.EXTRA_DATETIME_FORMATS)
            except Exception as err2:
                err.add_note(f"-> {err2}")

            # Try to parse datetime object with chinese regex
            try:
                return parse_by_chinese_regex(dt_obj)
            except Exception as err3:
                err.add_note(f"-> {err3}")

            # Raise error if all methods failed
            raise err

        # If the input is a str or int, full parse workflow
        if (_type_ := type(dt_obj)) in (str, int):
            return full_parse_workflow(dt_obj, *formats)

        # Adapt to datetime
        if (adapter := _DT_ADAPTER_MAP.get(_type_)) is not None:
            return adapter(dt_obj)

        # Unsupported input type
        raise ValueError(
            f"<Python_Datetime> Unsupported dtype: {repr(dt_obj)} {_type_}"
        )

    def __to_year(self, dt: _datetime, year: int = None) -> _datetime:
        if not year:
            return dt
        elif 0 < year < 9999:
            return dt.replace(year=year)
        else:
            return dt.replace(year=9999)

    def __to_month(self, dt: _datetime, month: int = None) -> _datetime:
        if not month:
            return dt
        elif 0 < month < 12:
            return dt.replace(month=month)
        else:
            return dt.replace(month=12)

    def __to_day(self, dt: _datetime, day: int = None) -> _datetime:
        if not day:
            return dt
        elif 0 < day <= 28:
            return dt.replace(day=day)
        elif 28 < day < 31:
            return dt.replace(day=min(day, self.__month_max_days(dt)))
        else:
            return self.__month_last_day(dt)

    def __month_max_days(self, dt: _datetime) -> int:
        return _monthrange(dt.year, dt.month)[1]

    def __month_last_day(self, dt: _datetime) -> _datetime:
        return dt.replace(day=self.__month_max_days(dt))


class Pandas_Datetime:
    """A simple Class to parse most pandas `Timestamp` related Series into `Series <'Timestamp'>`,
    and provide some useful properties & functions to manipulate the Timestamp Series.

    :param series: pandas Series with datetime-like values
    :param format: The strftime to parse time, e.g. `"%Y/%m/%d"`
        - If not provided, will try to parse infer the format automatically.
        - See `strftime documentation <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior>`
          for more information on choices, though note that `"%f"` will parse all the way up to nanoseconds.
        - "ISO8601", to parse any `ISO8601 <https://en.wikipedia.org/wiki/ISO_8601>`_
          time string (not necessarily in exactly the same format);
        - "mixed", to infer the format for each element individually. This is risky,
          and you should probably use it along with `dayfirst`.

    :param dayfirst: Specify a date parse order if `Series` is str or is list-like - default: `False`.
        - If `True`, parses dates with the day first, e.g.
          `"10/11/12"` is parsed as: `2012-11-10`.
        - `dayfirst=True` is not strict, but will prefer to parse with day first.

    :param yearfirst: Specify a date parse order if `Series` is str or is list-like - default: `False`.
        - If `True` parses dates with the year first, e.g.
          `"10/11/12"` is parsed as: `2010-11-12`.
        - If both `dayfirst` and `yearfirst` are `True`, `yearfirst` is
          preceded (same as :mod:`dateutil`).
        - `yearfirst=True` is not strict, but will prefer to parse with year first.

    :param utc: Control timezone-related parsing, localization and conversion - default: `False`.
        - If `True`, the function *always* returns a timezone-aware
          UTC-localized `Series`. To do this, timezone-naive inputs are
          *localized* as UTC, while timezone-aware inputs are *converted* to UTC.
        - If `False`, inputs will not be coerced to UTC. Timezone-naive inputs
          will remain naive, while timezone-aware ones will keep their time offsets.
          Limitations exist for mixed offsets (typically, daylight savings), see:
          `Examples <to_datetime_tz_examples>` section for details.

    :param unit: The unit of the arg (D, s, ms, us, ns) denote the unit
        Example, with `unit='ms'`, this would calculate
        the number of milliseconds to the unix epoch start.
    """

    def __init__(
        self,
        series: _Series,
        *,
        format: str = None,
        dayfirst: bool = False,
        yearfirst: bool = False,
        utc: bool = False,
        unit: str = None,
    ) -> None:
        self.__format: str = format
        self.__dayfirst: bool = dayfirst
        self.__yearfirst: bool = yearfirst
        self.__utc: bool = utc
        self.__unit: str = unit
        self.__dts = self.__to_datetime(
            series,
            format=self.__format,
            dayfirst=self.__dayfirst,
            yearfirst=self.__yearfirst,
            utc=self.__utc,
            unit=self.__unit,
        )

    @property
    def dts(self) -> _Series:
        return self.__dts

    @property
    def dates(self) -> _Series:
        return self.dts.dt.date

    @property
    def times(self) -> _Series:
        return self.dts.dt.time

    @property
    def yesterday(self) -> _Series:
        return self.dts + _offsets.Day(1)

    @property
    def tomorrow(self) -> _Series:
        return self.dts - _offsets.Day(1)

    @property
    def monday(self) -> _Series:
        return self.dts + _TimedeltaIndex(-self.dts.dt.weekday, unit="D")

    @property
    def tuesday(self) -> _Series:
        return self.dts + _TimedeltaIndex(-self.dts.dt.weekday + 1, unit="D")

    @property
    def wednesday(self) -> _Series:
        return self.dts + _TimedeltaIndex(-self.dts.dt.weekday + 2, unit="D")

    @property
    def thursday(self) -> _Series:
        return self.dts + _TimedeltaIndex(-self.dts.dt.weekday + 3, unit="D")

    @property
    def friday(self) -> _Series:
        return self.dts + _TimedeltaIndex(-self.dts.dt.weekday + 4, unit="D")

    @property
    def saturday(self) -> _Series:
        return self.dts + _TimedeltaIndex(-self.dts.dt.weekday + 5, unit="D")

    @property
    def sunday(self) -> _Series:
        return self.dts + _TimedeltaIndex(-self.dts.dt.weekday + 6, unit="D")

    @property
    def month1stDay(self) -> _Series:
        return self.dts + _offsets.MonthEnd(0) - _offsets.MonthBegin(1)

    @property
    def monthlstDay(self) -> _Series:
        return self.dts + _offsets.MonthEnd(0)

    @property
    def monthDays(self) -> _Series:
        """How many days in the month for the `Series <'Timestamp'>`"""

        return self.__month_max_days(self.dts)

    def last_week(self, weekday: int | str = None) -> Self:
        """Manipulate the `Series <'Timestamp'>` series to last week.

        :param weekday: The specific weekday to be manipulated to.
            - If not provided, will default to the same weekday in last week
            - For `str` input, accepts: `Monday`, `monday`, `Mon', `Mon.`, `mon`, `mon.` ...
            - For `int` input, starts from `1` for `Monday`, ends at `7` for `Sunday`

        :raises `ValueError`: If the `weekday` input is not supported.
        """

        if not weekday:
            return self.__new(self.dts - _offsets.Day(7))

        if weekday not in TimeUtils.WEEKDAY_MATCH:
            raise ValueError(f"<last_week> Unsupported weekday input: {weekday}")

        return self.__new(
            self.dts
            + _TimedeltaIndex(
                -self.dts.dt.weekday - 7 + TimeUtils.WEEKDAY_MATCH[weekday], unit="D"
            )
        )

    def next_week(self, weekday: int | str = None) -> Self:
        """Manipulate the `Series <'Timestamp'>` to next week.

        :param weekday: The specific weekday to be manipulated to.
            - If not provided, will default to the same weekday in next week
            - For `str` input, accepts: `Monday`, `monday`, `Mon', `Mon.`, `mon`, `mon.` ...
            - For `int` input, starts from `1` for `Monday`, ends at `7` for `Sunday`

        :raises `ValueError`: If the `weekday` input is not supported.
        """

        if not weekday:
            return self.__new(self.dts + _offsets.Day(7))

        if weekday not in TimeUtils.WEEKDAY_MATCH:
            raise ValueError(f"<next_week> Unsupported weekday input: {weekday}")

        return self.__new(
            self.dts
            + _TimedeltaIndex(
                -self.dts.dt.weekday + TimeUtils.WEEKDAY_MATCH[weekday] + 7, unit="D"
            )
        )

    def curr_week(self, weekday: int | str = None) -> Self:
        """Manipulate the `Series <'Timestamp'>` to current week.

        :param weekday: The specific weekday to be manipulated to.
            - If not provided, no changes will be made
            - For `str` input, accepts: `Monday`, `monday`, `Mon', `Mon.`, `mon`, `mon.` ...
            - For `int` input, starts from `1` for `Monday`, ends at `7` for `Sunday`

        :raises `ValueError`: If the `weekday` input is not supported.
        """

        if not weekday:
            return self

        elif weekday not in TimeUtils.WEEKDAY_MATCH:
            raise ValueError(f"<curr_week> Unsupported weekday input: {weekday}")

        return self.__new(
            self.dts
            + _TimedeltaIndex(
                -self.dts.dt.weekday + TimeUtils.WEEKDAY_MATCH[weekday], unit="D"
            ),
        )

    def is_weekday(self, weekday: int | str) -> _Series:
        """Check if the `Series <'Timestamp'>` is a specific weekday.

        :param weekday: The specific weekday to be checked.
            - For `str` input, accepts: `Monday`, `monday`, `Mon', `Mon.`, `mon`, `mon.` ...
            - For `int` input, starts from `1` for `Monday`, ends at `7` for `Sunday`

        :raises `ValueError`: If the `weekday` input is not supported.
        :return: A `Series` of `bool` values for if weekday matched.
        """

        if weekday not in TimeUtils.WEEKDAY_MATCH:
            raise ValueError(f"<is_weekday> Unsupported weekday input: {weekday}")

        return self.dts.dt.weekday == TimeUtils.WEEKDAY_MATCH[weekday]

    def last_month(self, day: int = None) -> Self:
        """Manipulate the `Series <'Timestamp'>` to last month.

        :param day: The specific day to be manipulated to.
            - If not provided, will default to the same day in last month
            - For `day` < `0`, will default to the last day of last month
            - For `day` input exceeds the max days in last month, will also default
              to the last day of last month
        """

        return self.__new(self.__to_day(self.dts + _offsets.DateOffset(months=-1), day))

    def next_month(self, day: int = None) -> Self:
        """Manipulate the `Series <'Timestamp'>` to next month.

        :param day: The specific day to be manipulated to.
            - If not provided, will default to the same day in next month
            - For `day` < `0`, will default to the last day of next month
            - For `day` input exceeds the max days in next month, will also default
              to the last day of next month
        """

        return self.__new(self.__to_day(self.dts + _offsets.DateOffset(months=1), day))

    def curr_month(self, day: int = None) -> Self:
        """Manipulate the `Series <'Timestamp'>` to current month.

        :param day: The specific day to be manipulated to.
            - If not provided, no changes will be made
            - For `day` < `0`, will default to the last day of current month
            - For `day` input exceeds the max days in current month, will also default
              to the last day of current month
        """

        return self.__new(self.__to_day(self.dts, day))

    def to_month(self, month: int = None, day: int = None) -> Self:
        """Manipulate the `Series <'Timestamp'>` to specific month and day.

        :param month: The specific month to be manipulated to.
            - If not provided, month will not be changed
            - For `month` < `0` or `month` >= 12, will default to December

        :param day: The specific day to be manipulated to.
            - If not provided, day will not be changed
            - For `day` < `0`, will default to the last day of the specific month
            - For `day` input exceeds the max days in the specific month, will also default
              to the last day of the specific month
        """

        return self.__new(self.__to_day(self.__to_month(self.dts, month), day))

    def is_monthday(self, day: int) -> _Series:
        """Check if the `Series <'Timestamp'>` is a specific day in month.

        :param day: The specific day to be checked.
            - For `day` < `0`, will default to the last day of the specific month
            - For `day` input exceeds the max days in the specific month, will also default
              to the last day of the specific month

        :return: A `Series` of `bool` values for if monthday matched.
        """

        return self.dts.dt.day == self.__to_day(self.dts, day).dt.day

    def adjust(
        self,
        *,
        years: int = None,
        months: int = None,
        weeks: int = None,
        days: int = None,
        hours: int = None,
        minutes: int = None,
        seconds: int = None,
        microseconds: int = None,
    ) -> Self:
        """Adjust the `Series <'Timestamp'>` with the specific date & time difference.

        :param years: number of years to be adjusted.
        :param months: number of months to be adjusted.
        :param weeks: number of weeks to be adjusted.
        :param days: number of days to be adjusted.
        :param hours: number of hours to be adjusted.
        :param minutes: number of minutes to be adjusted.
        :param seconds: number of seconds to be adjusted.
        :param microseconds: number of microseconds to be adjusted.
        """

        params = {
            "years": years,
            "months": months,
            "weeks": weeks,
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "microseconds": microseconds,
        }
        if not (params := {k: v for k, v in params.items() if v}):
            return self

        # Perform adjustment
        return self.__new(self.dts + _offsets.DateOffset(**params))

    def replcae(
        self,
        *,
        year: int = None,
        month: int = None,
        day: int = None,
        hour: int = None,
        minute: int = None,
        second: int = None,
        microsecond: int = None,
    ) -> Self:
        """Replace the `Series <'Timestamp'>` with the specific date & times.

        :param year: The specific year to be replaced.
            - If not provided, year will not be changed

        :param month: The specific month to be replaced.
            - If not provided, month will not be changed
            - For `month` < `0` or `month` > 12, will default to December

        :param day: The specific day to be replaced.
            - If not provided, day will not be changed
            - For `day` < `0`, will default to the last day of the specific month
            - For `day` input exceeds the max days in the specific month, will also default
              to the last day of the specific month

        :param hour: The specific hour to be replaced.
            - If not provided, hour will not be changed
            - For `hour` < `0` or `hour` > 23, will default to 23

        :param minute: The specific minute to be replaced.
            - If not provided, minute will not be changed
            - For `minute` < `0` or `minute` > 59, will default to 59

        :param second: The specific second to be replaced.
            - If not provided, second will not be changed
            - For `second` < `0` or `second` > 59, will default to 59

        :param microsecond: The specific microsecond to be replaced.
            - If not provided, microsecond will not be changed
            - For `microsecond` < `0` or `microsecond` > 999999, will default to 999999
        """

        # replacement for year, month, day
        dts = self.__to_day(self.__to_month(self.__to_year(self.dts, year), month), day)

        # replacement for hours
        if hour:
            dts = dts + _TimedeltaIndex(
                -dts.dt.hour + hour if 0 < hour < 23 else -dts.dt.hour + 23, unit="h"
            )

        # replacement for minutes
        if minute:
            dts = dts + _TimedeltaIndex(
                -dts.dt.minute + minute if 0 < minute < 59 else -dts.dt.minute + 59,
                unit="m",
            )

        # replacement for seconds
        if second:
            dts = dts + _TimedeltaIndex(
                -dts.dt.second + second if 0 < second < 59 else -dts.dt.second + 59,
                unit="s",
            )

        # replacement for microseconds
        if microsecond:
            dts = dts + _TimedeltaIndex(
                -dts.dt.microsecond + microsecond
                if 0 < microsecond < 999999
                else -dts.dt.microsecond + 999999,
                unit="us",
            )

        # return new instance
        return self.__new(dts)

    # Core functions
    def __new(self, dts: _Series) -> Self:
        return self.__class__(
            dts,
            format=self.__format,
            dayfirst=self.__dayfirst,
            yearfirst=self.__yearfirst,
            utc=self.__utc,
            unit=self.__unit,
        )

    def __to_datetime(
        self,
        series: _Series,
        *,
        format: str = None,
        dayfirst: bool = False,
        yearfirst: bool = False,
        utc: bool = None,
        unit: str = None,
    ) -> _Series:
        # If series is already datetime, return directly
        if series.dtype == "datetime64[ns]":
            return series

        # Else try use pandas to_datetime to parse
        try:
            return _pd_to_datetime(
                series,
                format=format,
                dayfirst=dayfirst,
                yearfirst=yearfirst,
                utc=utc,
                unit=unit,
            )
        except Exception as err:
            raise ValueError(f"<Pandas_Datetime> unable to parse: {err}") from err

    def __to_year(self, dts: _Series, year: int = None) -> _Series:
        if not year:
            return dts
        else:
            return dts + _offsets.DateOffset(year=year)

    def __to_month(self, dts: _Series, month: int = None) -> _Series:
        if not month:
            return dts
        elif month == 1:
            return self.__year_first_month(dts)
        elif 1 < month < 12:
            return self.__year_first_month(dts) + _offsets.DateOffset(months=month - 1)
        else:
            return self.__year_last_month(dts)

    def __to_day(self, dts: _Series, day: int = None) -> _Series:
        if not day:
            return dts
        elif day == 1:
            return self.__month_first_day(dts)
        elif 1 < day < 28:
            return dts + _TimedeltaIndex(-dts.dt.day + day, unit="D")
        elif 28 < day < 31:
            days = self.__month_max_days(dts)
            days = days.where(days <= day, day)
            return dts + _TimedeltaIndex(-dts.dt.day + days, unit="D")
        else:
            return self.__month_last_day(dts)

    def __month_max_days(self, dts: _Series) -> _Series:
        return dts.dt.days_in_month

    def __month_first_day(self, dts: _Series) -> _Series:
        return dts + _offsets.MonthEnd(0) - _offsets.MonthBegin(1)

    def __month_last_day(self, dts: _Series) -> _Series:
        return dts + _offsets.MonthEnd(0)

    def __year_first_month(self, dts: _Series) -> _Series:
        return (
            dts
            + _offsets.YearEnd(0)
            - _offsets.YearBegin(1)
            + _TimedeltaIndex(dts.dt.day - 1, unit="D")
        )

    def __year_last_month(self, dts: _Series) -> _Series:
        return (
            dts
            + _offsets.YearEnd(0)
            + _TimedeltaIndex(-dts.dt.days_in_month + dts.dt.day, unit="D")
        )


# Parser =====================================================================================
_DEFAULT_PARSER = _dt_parser()


def parse(
    timestr: str,
    common_fmts: bool = False,
    *,
    default: _datetime = None,
    ignoretz: bool = False,
    tzinfos: dict[str, int] = None,
    dayfirst: bool = False,
    yearfirst: bool = False,
    fuzzy: bool = False,
) -> _datetime:
    """Parse the date/time string into a :class:`datetime.datetime` object.

    :param timestr:
        Any date/time string using the supported formats.

    :param common_fmts:
        - Try parsing with common formats. If hitted, can greatly improve
          performance. However, when missed, will introduce slight (20%)
          overhead to the overall parsing time.
        - Common formats:
        - "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
        - "%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d",
        - "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
        - "%H:%M:%S.%f", "%H:%M:%S"

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

    param dayfirst:
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

    return _DEFAULT_PARSER.parse(
        str(timestr),
        common_fmts,
        default or TimeUtils.DEFAULT_DATETIME,
        ignoretz,
        tzinfos,
        dayfirst,
        yearfirst,
        fuzzy,
    )


def _date_dt_adapter(dt_obj: _dt_date) -> _datetime:
    return _datetime.combine(dt_obj, TimeUtils.DEFAULT_TIME)


def _time_dt_adapter(dt_obj: _dt_time) -> _datetime:
    return _datetime.combine(TimeUtils.DEFAULT_DATE, dt_obj)


def _timestamp_dt_adapter(dt_obj: _Timestamp) -> _datetime:
    return dt_obj.to_pydatetime()


def _datetime64_dt_adapter(dt_obj: _datetime64) -> _datetime:
    return _Timestamp(dt_obj).to_pydatetime()


def _through(dt_obj: Any) -> _datetime:
    return dt_obj


_DT_ADAPTER_MAP: dict[type, Callable[[Any], _datetime]] = {
    _datetime: _through,
    _dt_date: _date_dt_adapter,
    _dt_time: _time_dt_adapter,
    _Timestamp: _timestamp_dt_adapter,
    _datetime64: _datetime64_dt_adapter,
}


def parse_adaptive(
    dt_obj: Any,
    common_fmts: bool = False,
    *,
    default: _datetime = None,
    ignoretz: bool = False,
    tzinfos: dict[str, int] = None,
    dayfirst: bool = False,
    yearfirst: bool = False,
    fuzzy: bool = False,
) -> _datetime:
    """Comparing to `parse`, this function also accepts: `date`, `time`,
    `datetime`, `Timestamp`, `datetime64` as input. Other behavior works
    exactly the same as the `parse` function."""

    # Parse str or int
    if (_type_ := type(dt_obj)) in (str, int):
        return parse(
            dt_obj,
            common_fmts=common_fmts,
            default=default,
            ignoretz=ignoretz,
            tzinfos=tzinfos,
            dayfirst=dayfirst,
            yearfirst=yearfirst,
            fuzzy=fuzzy,
        )

    # Adapt to datetime
    if (adatper := _DT_ADAPTER_MAP.get(_type_)) is not None:
        return adatper(dt_obj)

    # Unsupported input type
    raise ValueError(f"Unsupported dtype: {repr(dt_obj)} {_type_}")


def parse_common(timestr: str) -> _datetime:
    """Prase common date & time formats.

    Supported formats:
    - "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
    - "%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d",
    - "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
    - "%H:%M:%S.%f", "%H:%M:%S"

    :param timestr: Any date/time string using the supported formats.
    :return: Returns a :class:`datetime.datetime` object.
    """

    res = _parse_common(timestr)
    if res is None:
        raise ValueError(f"Can't parse string '{timestr}' with common formats")
    return res


def parse_exact(timestr: str, *formats: str) -> _datetime:
    """Prase date & time string with exact formats.

    :param timestr: Any date/time string using the supported formats.
    :param formats: Exact formats to parse the strings.
    :return: Returns a :class:`datetime.datetime` object.
    """

    res = _parse_exacts(timestr, formats)
    if res is None:
        raise ValueError(
            f"Can't parse string '{timestr}' with formats: {', '.join(formats)}"
        )
    return res


# functions ==================================================================================
_TIME_RANGE_UNIT: dict[str, dict[str, dict]] = {
    "year": {
        "start": {
            "month": 1,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "microsecond": 0,
        },
        "end": {
            "month": 12,
            "day": 31,
            "hour": 23,
            "minute": 59,
            "second": 59,
            "microsecond": 999999,
        },
    },
    "month": {
        "start": {"day": 1, "hour": 0, "minute": 0, "second": 0, "microsecond": 0},
        "end": {"hour": 23, "minute": 59, "second": 59, "microsecond": 999999},
    },
    "week": {
        "start": {"hour": 0, "minute": 0, "second": 0, "microsecond": 0},
        "end": {"hour": 23, "minute": 59, "second": 59, "microsecond": 999999},
    },
    "day": {
        "start": {"hour": 0, "minute": 0, "second": 0, "microsecond": 0},
        "end": {"hour": 23, "minute": 59, "second": 59, "microsecond": 999999},
    },
    "hour": {
        "start": {"minute": 0, "second": 0, "microsecond": 0},
        "end": {"minute": 59, "second": 59, "microsecond": 999999},
    },
    "minute": {
        "start": {"second": 0, "microsecond": 0},
        "end": {"second": 59, "microsecond": 999999},
    },
    "second": {
        "start": {"microsecond": 0},
        "end": {"microsecond": 999999},
    },
}


def cal_time_range(
    *,
    start: str | _dt_date | _datetime = None,
    end: str | _dt_date | _datetime = None,
    days: int = None,
    range_unit: str | None = "second",
    errors: str = "raise",
) -> tuple[_datetime, _datetime]:
    """Calculate the start and end `datetime` based on the given parameters.

    :param start, end, days: The time range parameters:
        - If `start` and `end` are provided -> return: (start_dt, end_dt)
        - If `start` and `days` are provided -> return: (start_dt, start_dt + (days - 1))
        - If `end` and `days` are provided -> return: (end_dt - (days - 1), end_dt)
        - If only `days` is provided -> return: (datetime.now() - (days - 1), datetime.now())
        - If only `start` is provided -> return: (start_dt, datetime.now())
        - If only `end` is provided -> return: (end_dt, end_dt)
        - If none of the params are given, check `errors` :param: explaination

    :param range_unit: adjust the calculated time range - `default`: `second`
        - Accepts: 'year', 'month', 'day', 'week', 'hour', 'minute', 'second',
          and None (implies no adjustment). 'week' is treated as 'day'.
        - This param adjusts the 'start' and 'end' time after the range calculation
          to the respective unit.
        - For example, if 'range_unit' is `'year'`, 'start' is adjusted to the start
          of the year (at 00:00:00 on Jan 1) and 'end' is adjusted to the end of
          the year (at 23:59:59.999999 on Dec 31).

    :param errors: how to handle errors - default: `raise`
        - This parameter only handle the error when no parameter is given.
        - `raise`: raise `ValueError` for not receiving any parameter
        - `ignore`: ignore the error and return `(None, None)`

    :return: (start_dt <`datetime`>, end_dt <`datetime`>)
    """

    # If 'start' and 'end' are provided
    if start is not None and end is not None:
        start_dt = Python_Datetime(start).dt
        end_dt = Python_Datetime(end).dt

    # If 'start' and 'days' are provided
    elif start is not None and days is not None:
        start_dt = Python_Datetime(start).dt
        end_dt = start_dt + _timedelta(days=days - 1)

    # If 'end' and 'days' are provided
    elif end is not None and days is not None:
        end_dt = Python_Datetime(end).dt
        start_dt = end_dt - _timedelta(days=days - 1)

    # If only 'days' is provided
    elif days is not None:
        end_dt = _datetime.now()
        start_dt = end_dt - _timedelta(days=days - 1)

    # If only 'start' is provided
    elif start is not None:
        start_dt = Python_Datetime(start).dt
        end_dt = _datetime.now()

    # If only 'end' is provided
    elif end is not None:
        start_dt = end_dt = Python_Datetime(end).dt

    # If none of the params are given
    else:
        if errors == "raise":
            raise ValueError(
                "<utils.cal_date_range> At least one parameter is required"
            )
        return None, None

    # Adjust start limit
    if start_dt > end_dt:
        _warn(
            "<utils.cal_time_range> "
            "The start '{}' is greater than the end '{}'. "
            "Consider swapping if not intended.".format(start_dt, end_dt),
            stacklevel=2,
        )
        start_dt = end_dt

    # Return without adjustment
    if not range_unit:
        return start_dt, end_dt

    # Execute unit adjustment
    if range_unit not in _TIME_RANGE_UNIT:
        raise ValueError(
            "The range_unit '{}' is not supported. Supports: {}".format(
                range_unit, ", ".join(_TIME_RANGE_UNIT.keys())
            )
        )
    start_dt = start_dt.replace(**_TIME_RANGE_UNIT[range_unit]["start"])
    if range_unit == "month":
        end_dt = end_dt.replace(
            day=_monthrange(end_dt.year, end_dt.month)[1],
            **_TIME_RANGE_UNIT[range_unit]["end"],
        )
    else:
        end_dt = end_dt.replace(**_TIME_RANGE_UNIT[range_unit]["end"])

    # Return adjusted time range
    return start_dt, end_dt


def gen_range_time(start: _datetime, end: _datetime, time_unit: str) -> list[_datetime]:
    """Using the given `start` and `end` datetime to generate a list of datetime

    :param start: Starting datetime
    :param end: Ending datetime
    :param time_unit: Time unit to generate the list of datetime, accpeted values:
        - `year`, `month`, `week`, `day`
        - *Notice: start of the week is `MONDAY`

    :return: list of datetime
        - If the `start` and `end` are in the same 'time_unit',
          return: `[start]`
        - If the `start` and `end` are in different 'time_unit',
          return: `[start, range_dt1, range_dt2..., end]`
    """

    if time_unit == "year":
        delta = Python_Datetime(start).delta(end, "Y", inclusive=False)
        if delta > 1:
            return (
                [start]
                + [start + ctimedelta_c(years=i) for i in range(1, delta)]
                + [end]
            )
        elif delta == 1:
            return [start, end]
        else:
            return [start]

    elif time_unit == "month":
        delta = Python_Datetime(start).delta(end, "M", inclusive=False)
        if delta > 1:
            return (
                [start]
                + [start + ctimedelta_c(months=i) for i in range(1, delta)]
                + [end]
            )
        elif delta == 1:
            return [start, end]
        else:
            return [start]

    elif time_unit == "week":
        delta = Python_Datetime(start).delta(end, "W", inclusive=False)
        if delta > 1:
            return (
                [start]
                + [start + _timedelta(days=i * 7) for i in range(1, delta)]
                + [end]
            )
        elif delta == 1:
            return [start, end]
        else:
            return [start]

    elif time_unit == "day":
        delta = Python_Datetime(start).delta(end, "D", inclusive=False)
        if delta > 1:
            return (
                [start] + [start + _timedelta(days=i) for i in range(1, delta)] + [end]
            )
        elif delta == 1:
            return [start, end]
        else:
            return [start]

    else:
        raise ValueError(
            "<gen_range_time> Only supports time_unit: "
            "'year', 'month', 'week', 'day'. Instead of: {} {}".format(
                time_unit, type(time_unit)
            )
        )


def unix_timestamp(utc: bool = False, ms: bool = False) -> int:
    """Simple function to get current timestamp.

    :param utc: If `True`, result will be a `UTC` timestamp else `local` timestamp.
    :param ms: If `True`, result will be a `millisecond` timestamp, else `second` timestamp.
    :return: `int` timestamp.
    """

    return _unix_timestamp(utc, ms)


def seconds_to_time(seconds: int) -> _dt_time:
    """Simple function to convert seconds to datetime.time.

    * Only support less then 24 hours of total seconds.

    :param seconds: `int` seconds.
    :return: `datetime.time`
    """

    return _seconds_to_time(int(seconds))


# ctimedelta =================================================================================
class ctimedelta:
    """The ctimedelta is completely based on dateutils.relativedelta. The only
    works that has been done is to convert the codes into cython. The result
    is some slight performance increase. All the credits should go to the
    original author of dateutils.relativedelta.

    There are two different ways to build a ctimedelta instance.

    ### The first method is passing it two date/datetime classes
    :param dt1: date | datetime object - `default`: `None`
    :param dt2: date | datetime object - `default`: `None`

    Example::
    >>> from dt_util import ctimedelta
        ctimedelta(datetime1, datetime2)

    ### The second method is passing it any number of the following keyword arguments
    #### Relative information:
    Notice `ONLY` accept integer due to cythonization, and can be negative
    (argument is plural); adding or subtracting a ctimedelta with relative
    information performs the corresponding arithmetic operation on the
    original datetime value with the information in the ctimedelta.

    :param years: relative years - `default`: `0`
    :param months: relative months - `default`: `0`
    :param days: relative days - `default`: `0`
    :param weeks: relative weeks - `default`: `0`
    :param hours: relative hours - `default`: `0`
    :param minutes: relative minutes - `default`: `0`
    :param seconds: relative seconds - `default`: `0`
    :param microseconds: relative microseconds - `default`: `0`

    #### Absolute information:
    Notice `ONLY` accept integer due to cythonization, and `-1` standards
    for None when comparing to original relativedelta. Adding or subtracting
    a ctimedelta with absolute information does not perform an arithmetic
    operation, but rather REPLACES the corresponding value in the
    original datetime with the value(s) in ctimedelta.

    :param year: absolute year - `default`: `-1`
    :param month: absolute month - `default`: `-1`
    :param day: absolute day - `default`: `-1`
    :param hour: absolute hour - `default`: `-1`
    :param minute: absolute minute - `default`: `-1`
    :param second: absolute second - `default`: `-1`
    :param microsecond: absolute microsecond - `default`: `-1`

    #### Weekday information:
    Notice `ONLY` accepts integer due to cythonization. This is different
    from the original relativedelta, which accepts a weekday object and
    allows arg like the nth Monday of the month. Due to cythonization,
    ctimedelta only accepts 0-6 as the weekday argument, where 0 is Monday
    and 6 is Sunday. Any value out of this will be defualt to -1 (None).

    :param weekday: absolute weekday - `default`: `-1`

    #### Leapdays information:
    Notice `ONLY` accepts integer due to cythonization. Will add given
    days to the date found, if year is a leap year, and the date found
    is post 28 of february.

    :param leapdays: relative leapdays - `default`: `0`

    #### Yearday information:
    Notice `ONLY` accepts integer due to cythonization. Set the yearday
    or the non-leap year day (jump leap days). These are converted to
    day/month/leapdays information.

    :param yearday: absolute yearday - `default`: `-1`
    :param nlyearday: absolute nlyearday - `default`: `-1`

    #### Argument order:
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

    Example::
    >>> from dt_util import ctimedelta
        from datetime import datetime
        dt = datetime(2018, 4, 9, 13, 37, 0)
        delta = ctimedelta(hours=25, day=1, weekday=1))
        dt + delta # result -> datetime.datetime(2018, 4, 2, 14, 37)
    """

    def __new__(cls, **kwarg):
        return ctimedelta_c(**kwarg)
