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
Tests of read_enbid_binary, which reads the densities EnBiD writes (in the GADGET format) when it is given
masses. The files are made by hand, with write_enbid_binary_output and struct, not by the code under test.
"""
import struct

import numpy as np
import pytest

from ..enbid_ananke import read_enbid_binary
from .utils import in_tmp_wd, write_enbid_binary_output


@in_tmp_wd
def test_the_densities_are_read_back():
    density = np.array([0.5, 1.25, 3.0, 1e6, 1e-6], dtype=np.float32)
    write_enbid_binary_output('density', density)
    rho = read_enbid_binary('density')
    assert rho.dtype == np.float32
    np.testing.assert_array_equal(rho, density)


@in_tmp_wd
def test_a_large_array_is_read_whole():
    density = np.random.default_rng(3).uniform(size=100000).astype(np.float32)
    write_enbid_binary_output('density', density)
    np.testing.assert_array_equal(read_enbid_binary('density'), density)


@in_tmp_wd
def test_no_particles_gives_an_empty_array():
    write_enbid_binary_output('density', [])
    rho = read_enbid_binary('density')
    assert rho.shape == (0,)


@in_tmp_wd
def test_anything_after_the_densities_is_ignored():
    write_enbid_binary_output('density', [1.0, 2.0])
    with open('density', 'ab') as f:
        f.write(b'trailing bytes that are not a block')
    np.testing.assert_array_equal(read_enbid_binary('density'), [1.0, 2.0])


@in_tmp_wd
def test_a_header_of_the_wrong_size_is_refused():
    with open('density', 'wb') as f:
        f.write(struct.pack('<i', 128) + bytes(128) + struct.pack('<i', 128))
    with pytest.raises(ValueError, match='256'):
        read_enbid_binary('density')


@in_tmp_wd
def test_an_empty_file_is_refused():
    open('density', 'wb').close()
    with pytest.raises(IOError):
        read_enbid_binary('density')


@in_tmp_wd
def test_a_file_with_a_header_only_is_refused():
    with open('density', 'wb') as f:
        f.write(struct.pack('<i', 256) + bytes(256) + struct.pack('<i', 256))
    with pytest.raises(IOError):
        read_enbid_binary('density')


@in_tmp_wd
def test_a_file_that_does_not_exist_is_refused():
    with pytest.raises(FileNotFoundError):
        read_enbid_binary('nothing here')


if __name__ == '__main__':
    pass
