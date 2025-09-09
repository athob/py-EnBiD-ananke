#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2022  Adrien CR Thob
#
# This file is part of py-EnBiD-ananke:
# <https://github.com/athob/py-EnBiD-ananke>.
# 
# The full copyright notice, including terms governing use, modification,
# and redistribution, is contained in the files LICENSE and COPYRIGHT,
# which can be found at the root of the source code distribution tree:
# - LICENSE <https://github.com/athob/py-EnBiD-ananke/blob/main/LICENSE>
# - COPYRIGHT <https://github.com/athob/py-EnBiD-ananke/blob/main/COPYRIGHT>
#
import pathlib

import numpy as np
from sklearn import neighbors as nghb

from ..enbid_ananke import write_for_enbid, DEFAULT_FOR_PARAMFILE, TTAGS
from .utils import n_sample, in_tmp_wd


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


if __name__ == '__main__':
    pass
