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
Tests of write_gadget_file, which writes the input EnBiD reads when it is given masses. The file is
parsed here byte by byte, with the layout of the GADGET-1 format, rather than with the code under test.
"""
import struct

import numpy as np
import pytest

from ..enbid_ananke import write_gadget_file
from .utils import in_tmp_wd, read_gadget_records

HEADER = '<6i6d2d2i6i2i4d3i'   # the 172 bytes of the header that are used, out of 256


def parse_header(block):
    assert len(block) == 256
    values = struct.unpack(HEADER, block[:struct.calcsize(HEADER)])
    assert block[struct.calcsize(HEADER):] == bytes(256 - struct.calcsize(HEADER))   # the rest is padding
    return dict(npart=values[0:6], massarr=values[6:12], time=values[12], redshift=values[13],
                nall=values[16:22], num_files=values[23], boxsize=values[24], omega0=values[25],
                omegalambda=values[26], hubble=values[27], flags_after_cosmology=values[28:31])


def sample(n=5, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(size=(n, 3)), rng.uniform(1, 2, size=n)


@in_tmp_wd
def test_the_file_is_five_blocks_of_the_right_sizes():
    pos, mass = sample(5)
    write_gadget_file('snapshot', pos, mass)
    blocks = read_gadget_records('snapshot')      # also checks the size before each block equals the one after
    # header, positions, velocities, ids, masses
    assert [len(block) for block in blocks] == [256, 5 * 12, 5 * 12, 5 * 4, 5 * 4]


@in_tmp_wd
def test_the_header_with_its_defaults():
    pos, mass = sample(5)
    write_gadget_file('snapshot', pos, mass)
    header = parse_header(read_gadget_records('snapshot')[0])
    assert header['npart'] == (0, 5, 0, 0, 0, 0)          # particle type 1 by default
    assert header['nall'] == header['npart']
    assert header['massarr'] == (0.0,) * 6                # the masses are in their own block
    assert header['num_files'] == 1
    assert (header['time'], header['redshift'], header['boxsize'], header['omega0'], header['omegalambda']) == (0.0,) * 5
    assert header['hubble'] == 0.7
    assert header['flags_after_cosmology'] == (0, 0, 1)   # flag_id, flag_dim, flag_density


@in_tmp_wd
def test_the_header_carries_the_cosmological_parameters():
    pos, mass = sample(3)
    write_gadget_file('snapshot', pos, mass, boxsize=100.0, time=0.5, redshift=1.0,
                      omega0=0.3, omegalambda=0.7, hubble=0.68)
    header = parse_header(read_gadget_records('snapshot')[0])
    assert (header['boxsize'], header['time'], header['redshift']) == (100.0, 0.5, 1.0)
    assert (header['omega0'], header['omegalambda'], header['hubble']) == (0.3, 0.7, 0.68)


@pytest.mark.parametrize('particle_type', [0, 1, 2, 3, 4, 5])
@in_tmp_wd
def test_the_particles_are_counted_in_their_type(particle_type):
    pos, mass = sample(4)
    write_gadget_file('snapshot', pos, mass, particle_type=particle_type)
    header = parse_header(read_gadget_records('snapshot')[0])
    expected = [0] * 6
    expected[particle_type] = 4
    assert header['npart'] == tuple(expected) == header['nall']


@in_tmp_wd
def test_positions_and_masses_are_stored_as_single_precision():
    pos, mass = sample(7)                                  # float64 in
    write_gadget_file('snapshot', pos, mass)
    blocks = read_gadget_records('snapshot')
    np.testing.assert_array_equal(np.frombuffer(blocks[1], dtype='<f4').reshape(7, 3), pos.astype(np.float32))
    np.testing.assert_array_equal(np.frombuffer(blocks[4], dtype='<f4'), mass.astype(np.float32))


@in_tmp_wd
def test_ids_run_from_one():
    pos, mass = sample(6)
    write_gadget_file('snapshot', pos, mass)
    np.testing.assert_array_equal(np.frombuffer(read_gadget_records('snapshot')[3], dtype='<i4'), np.arange(1, 7))


@in_tmp_wd
def test_velocities_are_zero_unless_given():
    pos, mass = sample(4)
    write_gadget_file('without', pos, mass)
    np.testing.assert_array_equal(np.frombuffer(read_gadget_records('without')[2], dtype='<f4'), np.zeros(12))
    vel = sample(4, seed=7)[0]
    write_gadget_file('with', pos, mass, vel=vel)
    np.testing.assert_array_equal(np.frombuffer(read_gadget_records('with')[2], dtype='<f4').reshape(4, 3),
                                  vel.astype(np.float32))


@in_tmp_wd
def test_no_particles_gives_a_header_and_empty_blocks():
    write_gadget_file('snapshot', np.empty((0, 3)), np.empty(0))
    blocks = read_gadget_records('snapshot')
    assert [len(block) for block in blocks] == [256, 0, 0, 0, 0]
    assert parse_header(blocks[0])['npart'] == (0, 0, 0, 0, 0, 0)


@in_tmp_wd
def test_masses_and_positions_must_be_as_many():
    pos, mass = sample(5)
    with pytest.raises(ValueError):
        write_gadget_file('snapshot', pos, mass[:4])


@pytest.mark.parametrize('shape', [(4, 3), (5, 2), (5,)])
@in_tmp_wd
def test_velocities_must_be_n_by_three(shape):
    pos, mass = sample(5)
    with pytest.raises((ValueError, IndexError)):        # a 1D array fails on its second axis
        write_gadget_file('snapshot', pos, mass, vel=np.zeros(shape))


if __name__ == '__main__':
    pass
