#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from typing import Type
from json import load as _load, dump as _dump
from json import loads as _loads, dumps as _dumps

__all__ = ["load", "save", "parse", "serialize"]


# Load JSON file
def load(path: str, *, encoding: str = "utf-8") -> dict:
    """Load `json` file from a path"""

    if not path.endswith(".json"):
        path += ".json"

    try:
        with open(path, "r", encoding=encoding) as file:
            return _load(file)
    except Exception as err:
        err.add_note(f"<json_util.load> Failed to load json file from: '{path}'")
        raise


# Save JSON file
def save(
    obj: object,
    path: str,
    *,
    encoding: str = "utf-8",
    indent: int = 4,
    ensure_ascii: bool = True,
) -> None:
    """Save `json` object to a file (path)"""

    if not path.endswith(".json"):
        path += ".json"

    try:
        with open(path, "w", encoding=encoding) as file:
            _dump(obj, file, indent=indent, ensure_ascii=ensure_ascii)
    except Exception as err:
        err.add_note(f"<json_util.save> Failed to save json file to: '{path}'")
        raise


# Parse JSON
def parse(string: str) -> str | list | dict:
    """Parse serialized `json` string"""

    try:
        return _loads(string)
    except Exception as err:
        err.add_note(
            f"<json_util.parse> Failed to parse json string: '{string}' {type(string)}"
        )
        raise


# Serialize JSON
def serialize(
    obj: object,
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = True,
    default: Type = str,
) -> str:
    """Serialize object to `json` string"""

    try:
        return _dumps(
            obj,
            skipkeys=skipkeys,
            ensure_ascii=ensure_ascii,
            default=default,
        )
    except Exception as err:
        err.add_note(
            f"<json_util.serialize> Failed to serialize object: '{obj}' {type(obj)}"
        )
        raise
