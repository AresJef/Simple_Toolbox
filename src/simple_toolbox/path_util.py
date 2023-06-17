#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os as _os
import shutil as _shutil
from simple_toolbox.cython_core.path_util_c import list_directory
from simple_toolbox.cython_core.path_util_c import clean_path as _clean_path
from simple_toolbox.cython_core.path_util_c import offset_path as _offset_path

__all__ = [
    "clean",
    "abs",
    "exists",
    "offset",
    "make",
    "join",
    "list_dir",
    "move_dir",
    "copy_dir",
    "remove_dir",
    "move_file",
    "copy_file",
    "remove_file",
]


# Clean Path
def clean(path: str) -> str:
    """Remove all invalid speical characters for system directory path (Windows/MacOS/Linux)"""

    return _clean_path(path, _os.sep)


# Absolute Path
def abs(path: str) -> str:
    """Return the absolute path for a file or directory"""

    return _os.path.abspath(_os.path.dirname(path))


# Check Path Exists
def exists(path: str) -> bool:
    """Check if path exists"""

    return _os.path.exists(path)


# Offset Path
def offset(path: str, offsets: int = -1) -> str:
    """Offset path by a number of OS seperator (default: -1)

    Example:
    >>> base_path = "a/b/c/d/e/f/g"
    >>> offset_path(base_path, 2) #-> "c/d/e/f/g"
    >>> offset_path(base_path, -2) #> "a/b/c/d/e"
    """

    return _offset_path(path, offsets, _os.sep)


# Make Directory
def make(dir: str, offsets: int = 0) -> bool:
    """Make directory (path) if not exist

    :param dir: directory to create
    :param offsets: Offset directory by a number of OS seperator (default: 0)
    """

    if offsets:
        dir = offset(dir, offsets=offsets)
    if not exists(dir):
        _os.makedirs(dir)


# Join Path
def join(*paths: str) -> str:
    """Join string of paths into a single path"""

    return clean(_os.path.join(*paths))


# List Directory
def list_dir(dir: str, *excludes: str) -> list[str]:
    """List all the files and directories from a directory

    :param dir: directory
    :param excludes: file or folder name to be excluded from the list
        If no excludes are provided, the following files and folders will be
        excluded as default: ".DS_Store", "Thumbs.db", "desktop.ini", ".git", ".gitignore"
    :return: `list` of files and directories names
    """

    return list_directory(dir, excludes)


# Move Directory
def move_dir(src: str, dst: str) -> None:
    """Move directory from source to destination"""

    if exists(src):
        make(offset(dst, -1))
        _shutil.move(src, dst)


# Copy Directory
def copy_dir(src: str, dst: str) -> None:
    """Copy directory from source to destination"""

    if exists(src):
        make(offset(dst, -1))
        _shutil.copytree(src, dst)


# Delete Directory
def remove_dir(dir: str) -> None:
    """Delete directory"""

    if exists(dir):
        _shutil.rmtree(dir)


# Move File
def move_file(src: str, dst: str) -> None:
    """Move file from source to destination"""

    if exists(src):
        make(offset(dst, -1))
        _shutil.move(src, dst)


# Copy File
def copy_file(src: str, dst: str, fullMeta: bool = False) -> None:
    """Copy file from source to destination"""

    if exists(src):
        make(offset(dst, -1))
        if fullMeta:
            _shutil.copy2(src, dst)
        else:
            _shutil.copy(src, dst)


# Delete File
def remove_file(path: str) -> None:
    """Delete file"""

    if exists(path):
        _os.remove(path)
