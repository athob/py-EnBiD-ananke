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
        """
        Return the one instance of the class, creating it on the first call.

        Parameters
        ----------
        *args, **kwargs
            Passed to the class on the first call, when the instance is created; ignored afterwards.

        Returns
        -------
        instance
            The instance of the class.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def _execute_generator(args: Sequence[_StrPath], **kwargs: Any) -> Generator[str, None, None]:
    """
    Run a command, and give its output line by line as it prints it, errors included.

    Parameters
    ----------
    args : sequence of str or path
        The command and its arguments, which are not run through a shell.
    **kwargs
        Passed to subprocess.Popen (for instance ``cwd``).

    Yields
    ------
    line : str
        The lines the command writes to its output and its error stream, in the order it writes them.

    Raises
    ------
    subprocess.CalledProcessError
        After the last line, if the command exited with an error.
    """
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

    Parameters
    ----------
    args : sequence of str or path
        The command and its arguments, which are not run through a shell.
    verbose : bool, optional
        Whether to print the output of the command, errors included, as it
        comes. Default to True.
    **kwargs
        Passed to subprocess.Popen (for instance ``cwd``).

    Raises
    ------
    subprocess.CalledProcessError
        If the command exited with an error, once its output was read.
    FileNotFoundError
        If the command does not exist.
    """
    for path in _execute_generator(args, **kwargs):
        print(path, end="") if verbose else None


def get_version_of_command(cmd: str) -> str:
    """
    Give the version a command reports with ``--version``.

    Parameters
    ----------
    cmd : str
        The command, which has to be on the PATH.

    Returns
    -------
    version : str
        The first of the dotted numbers in what the command prints, such as
        ``"4.3"`` for ``GNU Make 4.3``.

    Raises
    ------
    FileNotFoundError
        If the command does not exist.
    subprocess.CalledProcessError
        If the command exited with an error.
    IndexError
        If what the command prints has no dotted number.
    """
    return re.findall(r"((?:[0-9]+\.)+[0-9]+)",
                      str(subprocess.check_output([cmd, '--version'])))[0]


def import_source_file(module_name: str, file_path: _StrPath) -> ModuleType:
    """
    Import a Python source file as a module of the given name.

    The module is registered in ``sys.modules``, and the file is read on every
    call, whatever was imported under that name before.

    Parameters
    ----------
    module_name : str
        The name the module is given.
    file_path : str or path
        The source file.

    Returns
    -------
    module : types.ModuleType
        The module.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    # based on https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    # (the spec and its loader are None for a file that is not Python source: that fails here as it always did)
    spec = cast(ModuleSpec, importlib.util.spec_from_file_location(module_name, file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    cast(Loader, spec.loader).exec_module(module)
    return module


if __name__ == '__main__':
    raise NotImplementedError()
