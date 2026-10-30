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
Tests of enbid with the real EnBiD, not a stand-in: they are run when the executables are built (installing
the package builds them), and skipped otherwise. What EnBiD returns is not known to the digit here, so they
check what any density estimator has to satisfy: one finite density per particle, the same answer for the
same question, no change when the data is moved as a whole, and a density that falls with the distance from
the center of a Gaussian cloud.
"""
import numpy as np
import pytest

from ..enbid_ananke import enbid, CONSTANTS
from .utils import in_tmp_wd

built = CONSTANTS.enbid3d.is_file() and CONSTANTS.enbid6d.is_file()
needs_enbid = pytest.mark.skipif(not built, reason="EnBiD is not built (installing the package builds it)")

N = 1000


def cloud(n=N, seed=42):
    return np.random.default_rng(seed).normal(size=(n, 3))


def spearman(a, b):
    """The correlation of the ranks of a and b: 1 if one rises with the other, -1 if it falls."""
    return np.corrcoef(np.argsort(np.argsort(a)), np.argsort(np.argsort(b)))[0, 1]


@needs_enbid
@in_tmp_wd
def test_one_finite_density_per_particle():
    rho = enbid(cloud(), name='run', verbose=False)
    assert rho.shape == (N,)
    assert np.isfinite(rho).all()
    assert (rho >= 0).all() and (rho > 0).mean() > 0.99


@needs_enbid
@in_tmp_wd
def test_the_density_falls_with_the_distance_from_the_center():
    points = cloud()
    rho = enbid(points, name='run', verbose=False)
    assert spearman(rho, np.linalg.norm(points, axis=1)) < -0.7


@needs_enbid
@in_tmp_wd
def test_the_same_input_gives_the_same_densities():
    first = enbid(cloud(), name='first', verbose=False)
    second = enbid(cloud(), name='second', verbose=False)
    np.testing.assert_allclose(first, second, rtol=1e-6)


@needs_enbid
@in_tmp_wd
def test_moving_the_data_as_a_whole_does_not_change_the_densities():
    points = cloud()
    reference = enbid(points, name='reference', verbose=False)
    moved = enbid(points + np.array([10.0, -5.0, 3.0]), name='moved', verbose=False)
    close = np.isclose(moved, reference, rtol=1e-4)
    assert close.mean() > 0.99                       # all of them, unless a rounding sent a particle to the other side of a split


@needs_enbid
@in_tmp_wd
def test_more_neighbours_make_a_smoother_estimate():
    points = cloud()
    rough = enbid(points, name='rough', ngb=16, verbose=False)
    smooth = enbid(points, name='smooth', ngb=128, verbose=False)
    assert np.std(np.log(smooth)) < np.std(np.log(rough))


@needs_enbid
@in_tmp_wd
def test_with_velocities_the_phase_space_density_has_one_value_per_particle():
    rho = enbid(cloud(), velocities=cloud(seed=7), name='run', verbose=False)
    assert rho.shape == (N,)
    assert np.isfinite(rho).all() and (rho >= 0).all()


@needs_enbid
@in_tmp_wd
def test_with_masses_the_densities_come_back_in_single_precision():
    rho = enbid(cloud(), mass=np.ones(N), name='run', verbose=False)
    assert rho.dtype == np.float32 and rho.shape == (N,)
    assert np.isfinite(rho).all() and (rho >= 0).all()


@needs_enbid
@in_tmp_wd
def test_with_caching_the_second_answer_is_the_first():
    first = enbid(cloud(), name='run', caching=True, verbose=False)
    second = enbid(cloud(), name='run', caching=True, verbose=False)
    np.testing.assert_array_equal(first, second)


if __name__ == '__main__':
    pass
