#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os as _os
import zipfile as _zipfile

__all__ = ["zip_folder"]


def zip_folder(src: str, dst: str) -> str:
    """Compress a folder to a zip file

    :param src: folder full directory to be compressed
    :param dst: the zip file full directory to be saved
    :return: the zip file full directory
    """

    # check zipfile path
    if not dst.endswith(".zip"):
        dst += ".zip"

    # zipfile handle
    ziph = _zipfile.ZipFile(dst, "w", _zipfile.ZIP_DEFLATED)

    # zip all files
    try:
        for root_dir, _, files in _os.walk(src):
            for file in files:
                ziph.write(
                    _os.path.join(root_dir, file),
                    _os.path.relpath(
                        _os.path.join(root_dir, file), _os.path.join(src, "..")
                    ),
                )
    except Exception as err:
        err.add_note(f"<zip_util.zip_folder> Unable to zip folder: '{src}' to: '{dst}'")
        raise

    # return zipfile path
    return dst
