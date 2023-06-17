#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from yaml import safe_load as _safe_load, safe_dump as _safe_dump

__all__ = ["load", "save"]


def load(path: str, *, encoding: int = "utf-8") -> dict:
    """Load `yaml` file from a `path`"""

    if not path.endswith(".yaml"):
        path += ".yaml"

    try:
        with open(path, "r", encoding=encoding) as file:
            return _safe_load(file)
    except Exception as err:
        err.add_note(f"<yaml_util.load> Unable to load yaml from: '{path}'")
        raise


def save(
    data: dict,
    path: str,
    *,
    encoding: str = "utf-8",
    default_flow_style: bool = False,
) -> None:
    """Save `yaml` object to a file (path)"""

    if not path.endswith(".yaml"):
        path += ".yaml"

    try:
        with open(path, "w", encoding=encoding) as file:
            _safe_dump(
                data, file, encoding=encoding, default_flow_style=default_flow_style
            )
    except Exception as err:
        err.add_note(f"<yaml_util.save> Unable to save yaml to: '{path}'")
        raise
