#!/usr/bin/env python
import pathlib

import numpy as np
from sklearn import neighbors as nghb

from ..EnBiD_ananke import write_for_enbid, TO_ENBID_FILENAME
from .utils import n_sample, in_tmp_wd


@in_tmp_wd
def test_data_writing(data=np.random.randn(n_sample,3), name='test'):
    path = write_for_enbid(data, name=name)
    assert isinstance(path, pathlib.Path)
    file = path / TO_ENBID_FILENAME
    points = np.asarray(data)
    NN = nghb.NearestNeighbors(n_neighbors=2)
    NN.fit(points)
    NN_distances = NN.kneighbors(points)[0][:,1]
    most_clustered_structure = points[NN_distances < np.median(NN_distances)]
    most_clustered_structure_center = np.average(most_clustered_structure, axis=0)
    np.testing.assert_array_almost_equal_nulp(np.loadtxt(file, delimiter=' '), points - most_clustered_structure_center)


if __name__ == '__main__':
    pass
