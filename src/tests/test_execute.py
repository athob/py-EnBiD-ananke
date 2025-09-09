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
import random

from ..enbid_ananke._builtin_utils import execute
from .utils import list_stdout


def _test_verbose(verbose):
    lines = [f'test{random.randrange(100)}' for n in range(10)]
    to_printf = "\n".join(lines)
    with list_stdout() as L:
        execute(['printf', f'{to_printf}'], verbose=verbose)
    return L, lines
    

def test_verbose_true():
    L, lines = _test_verbose(True)
    assert L == lines


def test_verbose_false():
    L, _ = _test_verbose(False)
    assert not(L)


if __name__ == '__main__':
    pass
