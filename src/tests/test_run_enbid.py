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
import pathlib
import subprocess

import numpy as np
import pytest

from ..enbid_ananke import CONSTANTS, DEFAULT_NGB, run_enbid
from .utils import (in_tmp_wd, make_enbid_test_exec, list_stdout, preserved_enbid_paths,
                    with_fake_enbid, read_paramfile)


def sample(n=20, seed=0):
    return np.random.default_rng(seed).normal(size=(n, 3))


def calls(path):
    """The executables that ran in the folder, in order (the fake EnBiD keeps that log)."""
    return (path / 'fake_enbid_calls').read_text().split()


@in_tmp_wd
def test_run_enbid():
    with preserved_enbid_paths():
        CONSTANTS.enbid3d = pathlib.Path("./enbid_tester").absolute()
        make_enbid_test_exec()
        with list_stdout() as L:
            run_enbid(np.empty((0, 3)), name='test', verbose=True)
    assert CONSTANTS.enbid_paramfile in L


@with_fake_enbid
def test_the_parameter_file_has_the_defaults():
    path = run_enbid(sample(), name='run')
    values = read_paramfile(path / CONSTANTS.enbid_paramfile)
    assert values['InitCondFile'] == 'to_enbid'
    assert values['ICFormat'] == '0'                                    # ASCII, without masses
    assert values['DesNumNgb'] == values['DesNumNgbA'] == str(DEFAULT_NGB)
    assert values['SnapshotFileBase'] == f'_d3n{DEFAULT_NGB}'


@with_fake_enbid
def test_ngb_sets_the_neighbours_and_names_the_output():
    values = read_paramfile(run_enbid(sample(), name='run', ngb=10) / CONSTANTS.enbid_paramfile)
    assert values['DesNumNgb'] == values['DesNumNgbA'] == '10'
    assert values['SnapshotFileBase'] == '_d3n10'


@with_fake_enbid
def test_ngb_a_sets_the_neighbours_of_the_anisotropic_kernel_only():
    values = read_paramfile(run_enbid(sample(), name='run', ngb=10, ngb_a=5) / CONSTANTS.enbid_paramfile)
    assert values['DesNumNgb'] == '10'
    assert values['DesNumNgbA'] == '5'


@with_fake_enbid
def test_the_other_keywords_set_the_parameters_of_the_same_name():
    path = run_enbid(sample(), name='run', type_of_kernel=2, spatial_scale=2.5, periodic_boundary_on=1)
    values = read_paramfile(path / CONSTANTS.enbid_paramfile)
    assert (values['TypeOfKernel'], values['SpatialScale'], values['PeriodicBoundaryOn']) == ('2', '2.5', '1')
    assert values['TypeOfSmoothing'] == '3'                             # what was not given keeps its default


@with_fake_enbid
def test_masses_select_the_gadget_format():
    path = run_enbid(sample(), mass=np.ones(20), name='run')
    assert read_paramfile(path / CONSTANTS.enbid_paramfile)['ICFormat'] == '1'


@with_fake_enbid
def test_velocities_select_the_6d_executable_and_name_the_output():
    path = run_enbid(sample(), velocities=sample(seed=1), name='run', ngb=8)
    assert calls(path) == ['Enbid.6d']
    assert read_paramfile(path / CONSTANTS.enbid_paramfile)['SnapshotFileBase'] == '_d6n8'


@with_fake_enbid
def test_without_velocities_the_3d_executable_runs():
    assert calls(run_enbid(sample(), name='run')) == ['Enbid.3d']


@with_fake_enbid
def test_the_executable_is_run_in_the_folder_of_the_data_and_leaves_its_files_there():
    path = run_enbid(sample(), name='run')
    assert (path / CONSTANTS.usedvalues).is_file()
    assert (path / 'to_enbid_d3n64.est').is_file()


@with_fake_enbid
def test_without_caching_it_runs_every_time():
    run_enbid(sample(), name='run')
    assert calls(run_enbid(sample(), name='run')) == ['Enbid.3d'] * 2


@with_fake_enbid
def test_with_caching_it_runs_once_for_the_same_data_and_parameters():
    run_enbid(sample(), name='run', caching=True)
    assert calls(run_enbid(sample(), name='run', caching=True)) == ['Enbid.3d']


@with_fake_enbid
def test_with_caching_it_runs_again_when_a_parameter_changes():
    run_enbid(sample(), name='run', caching=True)
    assert calls(run_enbid(sample(), name='run', caching=True, ngb=10)) == ['Enbid.3d'] * 2


@with_fake_enbid
def test_with_caching_it_runs_again_when_the_data_changes():
    run_enbid(sample(seed=0), name='run', caching=True)
    other = run_enbid(sample(seed=1), name='run', caching=True)
    assert calls(other) == ['Enbid.3d']                                 # its own folder: it is its first run there


@with_fake_enbid
def test_verbose_shows_what_the_executable_prints():
    with list_stdout() as shown:
        run_enbid(sample(), name='run', verbose=True)
    assert shown == [CONSTANTS.enbid_paramfile]


@with_fake_enbid
def test_not_verbose_shows_nothing():
    with list_stdout() as shown:
        run_enbid(sample(), name='run', verbose=False)
    assert not shown


@with_fake_enbid
def test_an_executable_that_fails_raises():
    CONSTANTS.enbid3d.write_text('#!/bin/sh\necho something went wrong\nexit 3\n')
    with pytest.raises(subprocess.CalledProcessError):
        run_enbid(sample(), name='run', verbose=False)


@with_fake_enbid
def test_an_executable_that_is_not_there_raises():
    CONSTANTS.enbid3d.unlink()
    with pytest.raises(FileNotFoundError):
        run_enbid(sample(), name='run')


@with_fake_enbid
def test_a_name_is_needed():
    with pytest.raises(NotImplementedError):
        run_enbid(sample())


if __name__ == '__main__':
    pass
