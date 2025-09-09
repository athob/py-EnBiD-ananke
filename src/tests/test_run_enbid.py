#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2022  Adrien CR Thob
#
# This file is part of the py-EnBiD-ananke project,
# <https://github.com/athob/py-EnBiD-ananke>,  which is licensed
# under the GNU General Public License v2.0 (GPL-2.0).
# 
# The full copyright notice, including terms governing use, modification,
# and redistribution, is contained in the files LICENSE and COPYRIGHT,
# which can be found at the root of the source code distribution tree:
# - LICENSE <https://github.com/athob/py-EnBiD-ananke/blob/main/LICENSE>
# - COPYRIGHT <https://github.com/athob/py-EnBiD-ananke/blob/main/COPYRIGHT>
#
import pathlib

from ..enbid_ananke import CONSTANTS, run_enbid
from .utils import in_tmp_wd, make_enbid_test_exec, list_stdout


@in_tmp_wd
def test_run_enbid():
    CONSTANTS.enbid = pathlib.Path("./enbid_tester").absolute()
    enbid_exec = make_enbid_test_exec()
    with list_stdout() as L:
        run_enbid(name='test', verbose=True)
    assert CONSTANTS.enbid_paramfile in L


# TODO add tests for run_enbids kwargs


if __name__ == '__main__':
    pass
