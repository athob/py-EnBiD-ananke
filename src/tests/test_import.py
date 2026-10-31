#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2026  Adrien CR Thob
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
Tests of importing the package: what runs when it is imported has to work the way Python can be run.
"""
import os
import pathlib
import subprocess
import sys

from ..enbid_ananke import run_enbid, DEFAULT_NGB

SRC = pathlib.Path(__file__).resolve().parents[1]


def import_the_package(*python_options):
    """Imports the package of this source tree in a Python of its own, and says how that went."""
    environment = dict(os.environ, PYTHONPATH=str(SRC))
    return subprocess.run([sys.executable, *python_options, '-c', 'import enbid_ananke'],
                          env=environment, capture_output=True, text=True, cwd=str(SRC))


def test_the_package_imports():
    result = import_the_package()
    assert result.returncode == 0, result.stderr


def test_the_package_imports_when_python_strips_the_docstrings():
    # python -OO removes them, and the documentation of run_enbid is completed with the default number of neighbours
    result = import_the_package('-OO')
    assert result.returncode == 0, result.stderr


def test_the_documentation_of_run_enbid_gives_the_default_number_of_neighbours():
    assert '{DEFAULT_NGB}' not in run_enbid.__doc__
    assert str(DEFAULT_NGB) in run_enbid.__doc__


if __name__ == '__main__':
    pass
