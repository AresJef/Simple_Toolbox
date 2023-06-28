#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import socket as _socket
from hashlib import md5 as _md5
from uuid import getnode as _uuid_getnode
from sys import platform as _sys_platform
from shutil import disk_usage as _disk_usage
from multiprocessing import cpu_count as _cpu_count
from psutil import virtual_memory as _virtual_memory
from subprocess import check_output as _check_output
from getmac import get_mac_address as _get_mac_address
from platform import processor as _processor, platform as _platform

__all__ = [
    "os",
    "version",
    "serial_number",
    "cpu_count",
    "cpu_type",
    "memory_size",
    "memory_free",
    "memory_used",
    "hdd_size",
    "hdd_free",
    "hdd_used",
    "local_ip",
    "mac_address",
    "sys_info",
    "sys_uuid",
]

_OS_MAP: dict[str, str] = {
    "darwin": "mac",
    "linux": "linux",
    "linux2": "linux",
    "win32": "win",
    "cygwin": "win",
    "msys": "win",
    "os2": "os2",
    "os2emx": "os2",
    "riscos": "riscos",
    "atheos": "atheos",
    "freebsd": "freebsd",
    "freebsd6": "freebsd",
    "freebsd7": "freebsd",
    "freebsd8": "freebsd",
    "freebsdN": "freebsd",
}


def os() -> str:
    """Get the name of the operating system.
    All possible values: `"mac"`, `"linux"`, `"win"`,
    `"os2"`, `"riscos"`, `"atheos"`, `"freebsd"`, `"unknown"`
    """

    return _OS_MAP.get(_sys_platform, "unknown")


def version() -> str:
    """Return the operating system version."""

    return _platform()


def serial_number() -> str:
    """Return the serial number of the computer."""

    if os() == "mac":
        return (
            _check_output(
                "system_profiler SPHardwareDataType | awk '/Serial Number/ {print $4}'",
                shell=True,
            )
            .strip()
            .decode("utf-8")
        )

    return str(_uuid_getnode())


def cpu_count() -> int:
    """Return the number of CPU core counts of
    the computer.
    """

    return _cpu_count()


def cpu_type() -> str:
    """Return the CPU type of the computer."""

    if os() == "mac":
        return (
            _check_output(
                "sysctl -n machdep.cpu.brand_string",
                shell=True,
            )
            .strip()
            .decode("utf-8")
        )

    return _processor()


def memory_size(unit: str = "GB") -> float:
    """Return the memory size of the computer.

    :param unit: unit of the memory size, default: `GB`.
        available units: `GB`, `MB`, `KB`, `Byte`
    """

    return _convert_unit(_virtual_memory().total, unit)


def memory_free(unit: str = "GB", percent: bool = False) -> float:
    """Return free memory size of the computer at the
    current state.

    :param unit: unit of the memory size, default: `GB`.
        available units: `GB`, `MB`, `KB`, `Byte`
    :param percent: whether to return the percentage of the
    available memory, default: `False`.
        - If `True`, the `unit` parameter is invalid and the
          return value is the percentage of the available memory.
        - If `False`, the return value is the available memory
          size in corresponding size `unit`.
    """

    if percent:
        return round(_virtual_memory().available / _virtual_memory().total, 4)

    return _convert_unit(_virtual_memory().available, unit)


def memory_used(unit: str = "GB", percent: bool = False) -> float:
    """Return used memory size of the computer at the
    current state.

    :param unit: unit of the memory size, default: `GB`.
        available units: `GB`, `MB`, `KB`, `Byte`
    :param percent: whether to return the percentage of
    the used memory, default: `False`.
        - If `True`, the `unit` parameter is invalid and
          the return value is the percentage of the used
          memory.
        - If `False`, the return value is the used memory
          size in corresponding size `unit`.
    """

    if percent:
        return round(1 - memory_free(percent=True), 4)

    return _convert_unit(_virtual_memory().total - _virtual_memory().available, unit)


def hdd_size(unit: str = "GB") -> float:
    """Return the hard disk size of the computer.

    :param unit: unit of the hard disk size, default: `GB`.
        available units: `GB`, `MB`, `KB`, `Byte`
    """

    total, _, _ = _disk_usage("/")
    return _convert_unit(total, unit)


def hdd_free(unit: str = "GB", percent: bool = False) -> float:
    """Return free hard disk size of the computer at
    the current state.

    :param unit: unit of the hard disk size, default: `GB`.
        available units: `GB`, `MB`, `KB`, `Byte`
    :param percent: whether to return the percentage of the
    available hard disk, default: `False`.
        - If `True`, the `unit` parameter is invalid and
          the return value is the percentage of the available
          hard disk.
        - If `False`, the return value is the available hard
          disk size in corresponding size `unit`.
    """

    total, _, free = _disk_usage("/")
    if percent:
        return round(free / total, 4)

    return _convert_unit(free, unit)


def hdd_used(unit: str = "GB", percent: bool = False) -> float:
    """Return used hard disk size of the computer at
    the current state.

    :param unit: unit of the hard disk size, default: `GB`.
        available units: `GB`, `MB`, `KB`, `Byte`
    :param percent: whether to return the percentage of the
    used hard disk, default: `False`.
        - If `True`, the `unit` parameter is invalid and the
          return value is the percentage of the used hard disk.
        - If `False`, the return value is the used hard disk
          size in corresponding size `unit`.
    """

    total, used, _ = _disk_usage("/")
    if percent:
        return round(used / total, 4)

    return _convert_unit(used, unit)


def _convert_unit(size: int, unit: str) -> float:
    if (unit_u := unit.upper()) == "GB":
        return round((size / 1_073_741_824), 2)
    elif unit_u == "MB":
        return round((size / 1_048_576), 2)
    elif unit_u == "KB":
        return round((size / 1_024), 2)
    else:
        return size


def local_ip() -> str | None:
    """Return the local IP address of the computer."""

    try:
        # Create a socket and connect to a remote server
        with _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM) as sock:
            # 8.8.8.8 is a public DNS server, port 80 is for HTTP
            sock.connect(("8.8.8.8", 80))
            # Get the local IP address assigned to the socket
            ip_addr = sock.getsockname()[0]
    except Exception:
        ip_addr = None
    finally:
        return ip_addr


def mac_address() -> str | None:
    """Return the MAC address of the computer."""

    ip_addr = local_ip()
    return _get_mac_address(ip=ip_addr) if ip_addr else None


def sys_info() -> dict[str, str | int | float]:
    """Return a full dict of system information
    of the computer.
    """

    return {
        "os": os(),
        "version": version(),
        "cpu_type": cpu_type(),
        "cpu_count": cpu_count(),
        "memory_size": memory_size(),
        "hdd_size": hdd_size(),
        "mac_address": mac_address(),
        "local_ip": local_ip(),
    }


def sys_uuid() -> str:
    """Return a unique identifier of the computer
    in `md5` hash format based on `sys_info()`.
    """

    return _md5(str(sys_info).encode("utf-8")).hexdigest()
