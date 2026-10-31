#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2022  Adrien CR Thob
#
# This file is part of the py-EnBiD-ananke project,
# <https://github.com/athob/py-EnBiD-ananke>,  which is licensed
# under the GNU General Public License v2.0 or later (GPL-2.0-or-later).
# 
# The full copyright notice, including terms governing use, modification,
# and redistribution, is contained in the files LICENSE and COPYRIGHT,
# which can be found at the root of the source code distribution tree:
# - LICENSE <https://github.com/athob/py-EnBiD-ananke/blob/main/LICENSE>
# - COPYRIGHT <https://github.com/athob/py-EnBiD-ananke/blob/main/COPYRIGHT>
#
"""
Module utilities using built-in implementation
"""
import os
import sys
from importlib.abc import Loader
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Any, Dict, Generator, IO, Sequence, Union, cast
import subprocess
import importlib.util
import re

__all__ = ['Singleton', 'execute', 'get_version_of_command', 'import_source_file']

_StrPath = Union[str, "os.PathLike[str]"]   # quoted: os.PathLike cannot be subscripted before Python 3.9


class Singleton(type):
    """
    Singleton metaclass.
    Credit https://stackoverflow.com/q/6760685
    """
    _instances: Dict[type, Any] = {}
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def _execute_generator(args: Sequence[_StrPath], **kwargs: Any) -> Generator[str, None, None]:
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, **kwargs)
    stdout = cast(IO[str], popen.stdout)   # a pipe was asked for above: it is there
    for stdout_line in iter(stdout.readline, ""):
        yield stdout_line 
    stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, args)


def execute(args: Sequence[_StrPath], verbose: bool = True, **kwargs: Any) -> None:
    """
    Run the command described by args, and use
    verbose kwarg to redirect output/error stream
    to python output stream.
    Credit https://stackoverflow.com/a/4417735
    """
    for path in _execute_generator(args, **kwargs):
        print(path, end="") if verbose else None


def get_version_of_command(cmd: str) -> str:
    return re.findall(r"((?:[0-9]+\.)+[0-9]+)",
                      str(subprocess.check_output([cmd, '--version'])))[0]


def import_source_file(module_name: str, file_path: _StrPath) -> ModuleType:
    # based on https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    # (the spec and its loader are None for a file that is not Python source: that fails here as it always did)
    spec = cast(ModuleSpec, importlib.util.spec_from_file_location(module_name, file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    cast(Loader, spec.loader).exec_module(module)
    return module


if __name__ == '__main__':
    raise NotImplementedError()
