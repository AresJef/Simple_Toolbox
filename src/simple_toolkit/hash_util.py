#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from hashlib import md5 as _hashlib_md5
from random import getrandbits as _getrandbits

__all__ = ["md5", "ramdon"]


def md5(obj: object) -> str:
    """Convert Object (that can be converted to string) to MD5 Hash

    :param obj: Object to be converted
    :return: MD5 Hash <'str'>
    """

    try:
        hash_val = str(obj).encode("utf-8")
    except Exception as err:
        err.add_note(
            f"<hash_util.md5> Unable to stringify & encode '{obj}' {type(obj)}"
        )
        raise
    else:
        return _hashlib_md5(hash_val).hexdigest()


def random(bits: int = 128) -> str:
    """Generate Random Hash

    :param bits: Length of the hash <'int'>
    :return: Random Hash <'str'>
    """
    return "%032x" % _getrandbits(bits)
