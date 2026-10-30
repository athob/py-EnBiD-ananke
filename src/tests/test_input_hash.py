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
Tests of the hash of the input data, which names the folder the input of a run is written in, and
tells whether what is there is still what was asked for (the caching).
"""
import re

import numpy as np

from ..enbid_ananke import __compute_input_hash, HASH_PREFIX_LEN


def sample(n=10, seed=0):
    return np.random.default_rng(seed).normal(size=(n, 3))


def test_the_hash_is_a_sha256_in_hexadecimal():
    assert re.fullmatch(r'[0-9a-f]{64}', __compute_input_hash(sample()))
    assert 0 < HASH_PREFIX_LEN <= 64


def test_the_same_data_gives_the_same_hash():
    assert __compute_input_hash(sample()) == __compute_input_hash(sample().copy())
    assert (__compute_input_hash(sample(), sample(seed=1), sample(seed=2)[:, 0]) ==
            __compute_input_hash(sample(), sample(seed=1), sample(seed=2)[:, 0]))


def test_the_positions_the_velocities_and_the_masses_each_change_the_hash():
    points, velocities, mass = sample(), sample(seed=1), sample(seed=2)[:, 0]
    hashes = {
        __compute_input_hash(points),
        __compute_input_hash(sample(seed=5)),
        __compute_input_hash(points, velocities),
        __compute_input_hash(points, None, mass),
        __compute_input_hash(points, velocities, mass),
        __compute_input_hash(points, velocities, mass * 2),
    }
    assert len(hashes) == 6


def test_one_value_changing_changes_the_hash():
    points = sample()
    other = points.copy()
    other[3, 1] += 1e-12
    assert __compute_input_hash(points) != __compute_input_hash(other)


def test_the_precision_of_the_data_counts():
    points = sample()
    assert __compute_input_hash(points) != __compute_input_hash(points.astype(np.float32))


def test_the_split_of_the_data_into_positions_and_velocities_counts():
    # the same bytes, one after the other: 10 particles, or 5 particles and 5 velocities
    points = sample(10)
    assert __compute_input_hash(points) != __compute_input_hash(points[:5], points[5:])


def test_the_shape_of_the_data_counts():
    points = sample(10)
    assert __compute_input_hash(points) != __compute_input_hash(points.reshape(5, 6))
    assert __compute_input_hash(points) != __compute_input_hash(points.ravel())


def test_velocities_that_are_empty_are_not_no_velocities():
    points = sample(10)
    assert __compute_input_hash(points) != __compute_input_hash(points, np.empty((0, 3)))
    assert __compute_input_hash(points) != __compute_input_hash(points, None, np.empty(0))


def test_the_same_numbers_as_velocities_and_as_masses_are_not_the_same_input():
    points, numbers = sample(6), np.arange(6.0)
    assert __compute_input_hash(points, np.column_stack([numbers] * 3)) != __compute_input_hash(points, None, numbers)


def test_the_layout_in_memory_does_not_count():
    points = sample(10)
    assert __compute_input_hash(points) == __compute_input_hash(np.asfortranarray(points))
    assert __compute_input_hash(points[::2]) == __compute_input_hash(points[::2].copy())


if __name__ == '__main__':
    pass
