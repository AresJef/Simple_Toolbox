#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import asyncio
from math import floor as _math_floor
from time import perf_counter as _perf_counter
from simple_toolbox.dt_util import seconds_to_time as _seconds_to_time

__all__ = ["ProgressBar"]


# Custom Async Progress Bar
class ProgressBar:
    def __init__(
        self,
        desc: str = None,
        bar_width: int = 80,
        total_width: int = 120,
        frequency: int = 1,
        count: bool = True,
        percent: bool = True,
        speed: bool = True,
        timer: bool = True,
        eta: bool = True,
        style: str = "▇",
    ) -> None:
        # params
        self.__desc: str = desc
        self.__bar_width: int = bar_width - 2
        if not isinstance(self.__bar_width, int) or self.__bar_width < 30:
            raise ValueError("<Progress_Bar> `bar_width` must be greater than 32")
        self.__extra_width: int = total_width - self.__bar_width
        self.__frequency: int = frequency
        self.__count: bool = count
        self.__percent: bool = percent
        self.__speed: bool = speed
        self.__timer: bool = timer
        self.__eta: bool = eta
        self.__style: str = style
        # track
        self.__total: int = 0
        self.__finish: int = 0
        self.__start_time: float = 0
        # handle
        self.__finish_setup: bool = False
        self.__finish_print: bool = False

    @property
    def _progress(self) -> int:
        if self.__total == 0:
            return 0
        return int((self.__finish / self.__total) * 100)

    @property
    def _startTime(self) -> float:
        if self.__start_time == 0:
            self.__start_time = _perf_counter()
        return self.__start_time

    @property
    def _runTime(self) -> float:
        return _perf_counter() - self.__start_time

    @property
    def _speed(self) -> float:
        return self.__finish / self._runTime

    @property
    def _eta(self) -> float:
        if self.__total == 0:
            return 0
        if self._speed == 0:
            return 0
        return (self.__total - self.__finish) / self._speed

    @property
    def __bar(self) -> float:
        if self.__total == 0:
            return "|" + " " * self.__bar_width + "|"

        count = _math_floor(self.__finish / self.__total * self.__bar_width)
        return "|" + self.__style * count + " " * (self.__bar_width - count) + "|"

    async def setup(self, total: int) -> None:
        if not isinstance(total, int) or total <= 0:
            raise ValueError("<Progress_Bar> `total` tasks must be a positive integer")

        # track
        self.__reset()
        self.__total: int = total
        self.__finish_setup = True

    async def show(self, finish: int) -> None:
        if not self.__finish_setup:
            raise RuntimeError("<Progress_Bar.show> please call setup() method first")

        self.__finish = finish
        if self.__finish < self.__total:
            print(
                self.__format().ljust(self.__bar_width + self.__extra_width), end="\r"
            )
            await asyncio.sleep(self.__frequency)
        else:
            await self.finish()

    async def finish(self) -> None:
        if not self.__finish_setup:
            return None

        self.__finish = self.__total
        if not self.__finish_print:
            print(self.__format().ljust(self.__bar_width + self.__extra_width))
            self.__finish_print = True

    def __format(self) -> str:
        frt = []
        if self.__desc:
            frt.append(self.__desc)
        frt.append(self.__bar)
        if self.__count:
            frt.append("%s/%s" % (self.__finish, self.__total))
        if self.__percent:
            frt.append("%s%" % self._progress)
        if self.__speed:
            frt.append("%s/s" % round(self._speed, 1))
        if self.__timer:
            frt.append("run %s" % _seconds_to_time(self._runTime))
        if self.__eta:
            frt.append("eta %s" % _seconds_to_time(self._eta))
        return " ".join(frt)

    def __reset(self) -> None:
        self.__total: int = 0
        self.__finish: int = 0
        self.__start_time: float = _perf_counter()

    def __bool__(self) -> bool:
        return self.__finish < self.__total
