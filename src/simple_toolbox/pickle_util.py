#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from pickle import dump as _dump, load as _load

__all__ = ["load", "save"]


def load(path: str, *, encoding: str = "ASCII", errors: str = "strict") -> object:
    """Load pickled object from a path

    :param path: path of pickled object to be loaded
    :return: unpickled object
    """

    if not path.endswith(".pkl"):
        path += ".pkl"

    try:
        with open(path, "rb") as file:
            return _load(file, encoding=encoding, errors=errors)
    except Exception as err:
        err.add_note(f"<pickle_util.load> Unable to load pickle from: '{path}'")
        raise


def save(obj: object, path: str) -> None:
    """Save object as pickle to a path

    :param obj: object to be saved as pickle
    :param path: save path
    """

    if not path.endswith(".pkl"):
        path += ".pkl"

    try:
        with open(path, "wb") as file:
            _dump(obj, file)
    except Exception as err:
        err.add_note(f"<pickle_util.save> Unable to save pickle to: '{path}'")
        raise
