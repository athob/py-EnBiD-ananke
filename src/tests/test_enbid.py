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
Tests of enbid, the function the package is for: the densities of a set of particles. EnBiD is replaced
by a stand-in (see fake_enbid in utils.py) that returns 1, 2, 3... for particles without masses, and ten
times their mass for particles with masses, so that what comes back can be checked against what went in.
"""
import pathlib

import numpy as np
import pytest

from ..enbid_ananke import enbid, CONSTANTS
from .utils import with_fake_enbid, read_paramfile, preserved_enbid_paths, in_tmp_wd


def sample(n=20, seed=0):
    return np.random.default_rng(seed).normal(size=(n, 3))


def runs(name):
    """The folders where something was run under that name, and how many times each executable ran there."""
    folders = sorted(p for p in pathlib.Path(name).iterdir() if p.is_dir())
    return folders, [(p / 'fake_enbid_calls').read_text().split() for p in folders]


@with_fake_enbid
def test_one_density_per_particle_in_the_order_of_the_particles():
    rho = enbid(sample(20), name='run', verbose=False)
    assert rho.shape == (20,)
    np.testing.assert_array_equal(rho, np.arange(1, 21))


@with_fake_enbid
def test_with_masses_the_densities_come_from_the_gadget_output():
    mass = np.random.default_rng(1).uniform(1, 2, size=20)
    rho = enbid(sample(20), mass=mass, name='run', verbose=False)
    assert rho.dtype == np.float32                                       # what the binary output holds
    np.testing.assert_allclose(rho, 10 * mass.astype(np.float32))


@with_fake_enbid
def test_with_velocities_the_6d_executable_runs():
    enbid(sample(), velocities=sample(seed=1), name='run', verbose=False)
    assert runs('run')[1] == [['Enbid.6d']]


@with_fake_enbid
def test_with_velocities_and_masses_the_6d_executable_returns_the_densities_of_the_masses():
    mass = np.full(20, 3.0)
    rho = enbid(sample(), velocities=sample(seed=1), mass=mass, name='run', verbose=False)
    np.testing.assert_allclose(rho, 30.0)
    assert runs('run')[1] == [['Enbid.6d']]


@with_fake_enbid
def test_the_arguments_of_run_enbid_are_passed_on():
    enbid(sample(), name='run', ngb=7, ngb_a=3, type_of_kernel=2, verbose=False)
    folders, _ = runs('run')
    values = read_paramfile(folders[0] / CONSTANTS.enbid_paramfile)
    assert (values['DesNumNgb'], values['DesNumNgbA'], values['TypeOfKernel']) == ('7', '3', '2')


@with_fake_enbid
def test_the_input_can_be_a_list_of_lists():
    rho = enbid(sample(4).tolist(), name='run', verbose=False)
    np.testing.assert_array_equal(rho, [1, 2, 3, 4])


@with_fake_enbid
def test_it_runs_every_time_unless_caching_is_asked_for():
    enbid(sample(), name='run', verbose=False)
    enbid(sample(), name='run', verbose=False)
    assert runs('run')[1] == [['Enbid.3d', 'Enbid.3d']]


@with_fake_enbid
def test_caching_makes_it_run_once_for_the_same_input():
    first = enbid(sample(), name='run', caching=True, verbose=False)
    second = enbid(sample(), name='run', caching=True, verbose=False)
    np.testing.assert_array_equal(first, second)
    assert runs('run')[1] == [['Enbid.3d']]


@with_fake_enbid
def test_a_name_is_needed():
    # Without one, a temporary folder is meant to be used: for now, this is not implemented.
    with pytest.raises(NotImplementedError):
        enbid(sample())


@in_tmp_wd
def test_the_real_paths_of_the_executables_are_back_after_the_other_tests():
    # a test that changes the paths in CONSTANTS puts them back (preserved_enbid_paths)
    before = CONSTANTS.enbid3d, CONSTANTS.enbid6d
    with preserved_enbid_paths():
        CONSTANTS.enbid3d = pathlib.Path('somewhere else').absolute()
        CONSTANTS.enbid6d = pathlib.Path('and elsewhere').absolute()
    assert (CONSTANTS.enbid3d, CONSTANTS.enbid6d) == before
    assert CONSTANTS.enbid3d.parent.name == CONSTANTS.enbid6d.parent.name == CONSTANTS.enbid2   # the real ones


if __name__ == '__main__':
    pass
