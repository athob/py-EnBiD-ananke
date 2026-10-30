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

import numpy as np
import pytest
from sklearn import neighbors as nghb

from ..enbid_ananke import write_for_enbid, __compute_input_hash, DEFAULT_FOR_PARAMFILE, TTAGS, HASH_EXT, HASH_PREFIX_LEN
from .utils import n_sample, in_tmp_wd, read_gadget_records

INPUT_FILE = DEFAULT_FOR_PARAMFILE[TTAGS.fname]


def sample(n=20, seed=0):
    return np.random.default_rng(seed).normal(size=(n, 3))


@in_tmp_wd
def test_data_writing(data=np.random.randn(n_sample,3), name='test'):
    path = write_for_enbid(data, name=name)
    assert isinstance(path, pathlib.Path)
    file = path / DEFAULT_FOR_PARAMFILE[TTAGS.fname]
    points = np.asarray(data)
    NN = nghb.NearestNeighbors(n_neighbors=2)
    NN.fit(points)
    NN_distances = NN.kneighbors(points)[0][:,1]
    most_clustered_structure = points[NN_distances < np.median(NN_distances)]
    most_clustered_structure_center = np.average(most_clustered_structure, axis=0)
    np.testing.assert_array_almost_equal_nulp(np.loadtxt(file, delimiter=' '), points - most_clustered_structure_center)


@in_tmp_wd
def test_the_files_are_in_a_folder_named_after_the_data():
    points = sample()
    path = write_for_enbid(points, name='run/one')
    full_hash = __compute_input_hash(points)
    assert path == pathlib.Path('run/one') / full_hash[:HASH_PREFIX_LEN]
    assert (path / INPUT_FILE).is_file()
    assert (path / f"{INPUT_FILE}.{HASH_EXT}").read_bytes() == full_hash.encode('ascii')   # the whole hash is kept


@in_tmp_wd
def test_other_data_goes_to_another_folder_of_the_same_name():
    first, second = write_for_enbid(sample(seed=0), name='run'), write_for_enbid(sample(seed=1), name='run')
    assert first != second and first.parent == second.parent == pathlib.Path('run')


@in_tmp_wd
def test_centering_the_data_is_a_translation():
    points = sample()
    written = np.loadtxt(write_for_enbid(points, name='run') / INPUT_FILE)
    shift = written - points
    np.testing.assert_allclose(shift, np.broadcast_to(shift[0], shift.shape), atol=1e-12)   # the same for every particle
    assert np.abs(shift[0]).max() > 0


@in_tmp_wd
def test_velocities_make_six_columns_and_are_not_translated():
    points, velocities = sample(), sample(seed=1)
    written = np.loadtxt(write_for_enbid(points, velocities=velocities, name='run') / INPUT_FILE)
    assert written.shape == (20, 6)
    np.testing.assert_array_equal(written[:, 3:], velocities)
    np.testing.assert_allclose(np.diff(written[:, :3], axis=0), np.diff(points, axis=0), atol=1e-12)


@in_tmp_wd
def test_masses_make_a_gadget_file():
    points, mass = sample(), np.random.default_rng(2).uniform(1, 2, size=20)
    blocks = read_gadget_records(write_for_enbid(points, mass=mass, name='run') / INPUT_FILE)
    assert [len(block) for block in blocks] == [256, 20 * 12, 20 * 12, 20 * 4, 20 * 4]
    np.testing.assert_array_equal(np.frombuffer(blocks[4], dtype='<f4'), mass.astype(np.float32))
    stored = np.frombuffer(blocks[1], dtype='<f4').reshape(20, 3)
    np.testing.assert_allclose(np.diff(stored, axis=0), np.diff(points, axis=0), atol=1e-5)   # translated, in single precision


@in_tmp_wd
def test_masses_and_velocities_both_go_in_the_gadget_file():
    points, velocities, mass = sample(), sample(seed=1), np.ones(20)
    blocks = read_gadget_records(write_for_enbid(points, velocities=velocities, mass=mass, name='run') / INPUT_FILE)
    np.testing.assert_array_equal(np.frombuffer(blocks[2], dtype='<f4').reshape(20, 3), velocities.astype(np.float32))


@in_tmp_wd
def test_no_particles_gives_an_empty_file_and_its_hash():
    path = write_for_enbid(np.empty((0, 3)), name='run')
    assert (path / INPUT_FILE).read_text() == ''
    assert (path / f"{INPUT_FILE}.{HASH_EXT}").is_file()


@in_tmp_wd
def test_the_input_can_be_a_list_of_lists():
    points = sample(5).tolist()
    assert np.loadtxt(write_for_enbid(points, name='run') / INPUT_FILE).shape == (5, 3)


@in_tmp_wd
def test_without_caching_the_file_is_written_again():
    path = write_for_enbid(sample(), name='run')
    (path / INPUT_FILE).write_text('changed')
    write_for_enbid(sample(), name='run')
    assert (path / INPUT_FILE).read_text() != 'changed'


@in_tmp_wd
def test_with_caching_the_file_of_the_same_data_is_kept():
    path = write_for_enbid(sample(), name='run', caching=True)
    (path / INPUT_FILE).write_text('changed')
    assert write_for_enbid(sample(), name='run', caching=True) == path
    assert (path / INPUT_FILE).read_text() == 'changed'


@in_tmp_wd
def test_with_caching_the_file_is_written_again_if_the_hash_file_does_not_match():
    path = write_for_enbid(sample(), name='run', caching=True)
    (path / INPUT_FILE).write_text('changed')
    (path / f"{INPUT_FILE}.{HASH_EXT}").write_bytes(b'not the hash')
    write_for_enbid(sample(), name='run', caching=True)
    assert (path / INPUT_FILE).read_text() != 'changed'


@pytest.mark.parametrize('missing', [INPUT_FILE, f"{INPUT_FILE}.{HASH_EXT}"])
@in_tmp_wd
def test_with_caching_the_file_is_written_again_if_one_of_the_two_files_is_missing(missing):
    path = write_for_enbid(sample(), name='run', caching=True)
    (path / INPUT_FILE).write_text('changed')
    (path / missing).unlink()
    write_for_enbid(sample(), name='run', caching=True)
    assert (path / INPUT_FILE).read_text() != 'changed'


# The shapes are checked with assert statements today, which Python skips under -O: either error is accepted,
# so that checking them another way does not need these tests to change.
INVALID = (AssertionError, ValueError)


@pytest.mark.parametrize('points', [np.zeros((5, 2)), np.zeros((5, 4)), np.zeros(5), np.zeros((2, 5, 3))])
@in_tmp_wd
def test_the_positions_must_be_n_by_three(points):
    with pytest.raises(INVALID):
        write_for_enbid(points, name='run')


@pytest.mark.parametrize('velocities', [np.zeros((4, 3)), np.zeros((5, 2)), np.zeros(5)])
@in_tmp_wd
def test_the_velocities_must_be_n_by_three_and_as_many_as_the_positions(velocities):
    with pytest.raises(INVALID):
        write_for_enbid(np.zeros((5, 3)), velocities=velocities, name='run')


@pytest.mark.parametrize('mass', [np.ones(4), np.ones(6), np.ones((5, 1))])
@in_tmp_wd
def test_the_masses_must_be_one_per_particle(mass):
    with pytest.raises(INVALID):
        write_for_enbid(np.zeros((5, 3)), mass=mass, name='run')


@in_tmp_wd
def test_a_name_is_needed():
    with pytest.raises(NotImplementedError):      # a temporary folder is a TODO of the package
        write_for_enbid(sample())


if __name__ == '__main__':
    pass
