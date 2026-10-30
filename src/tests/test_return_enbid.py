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
import random

import numpy as np
import pytest

from ..enbid_ananke import return_enbid
from .utils import in_tmp_wd, simulate_enbid_output


@in_tmp_wd
def test_return_enbid():
    name = 'test'
    tag = '_d3n64'
    values = [random.randrange(1000000)/1000 for n in range(20)]
    simulate_enbid_output(name, tag, values)
    rho = return_enbid(name)
    np.testing.assert_array_almost_equal_nulp(rho, values)


@in_tmp_wd
def test_return_enbid_reads_the_binary_output_when_the_run_used_masses():
    values = np.array([0.5, 2.0, 7.25, 100.0], dtype=np.float32)
    simulate_enbid_output('test', '_d3n64', values, binary=True)
    rho = return_enbid('test')
    assert rho.dtype == np.float32
    np.testing.assert_array_equal(rho, values)


@in_tmp_wd
def test_return_enbid_reads_the_file_of_the_snapshot_base_the_run_used():
    simulate_enbid_output('test', '_d6n32', [1.0, 2.0, 3.0])
    np.testing.assert_array_equal(return_enbid('test'), [1.0, 2.0, 3.0])


@in_tmp_wd
def test_return_enbid_needs_the_files_of_a_run():
    with pytest.raises(FileNotFoundError):
        return_enbid('a folder where nothing was run')


if __name__ == '__main__':
    pass
