#!/usr/bin/env python
import pathlib

import numpy as np

from ..EnBiD_ananke import write_for_enbid, TO_ENBID_FILENAME
from .utils import n_sample, in_tmp_wd


@in_tmp_wd
def test_data_writing(data=np.random.randn(n_sample,3), name='test'):
    path = write_for_enbid(data, name=name)
    assert isinstance(path, pathlib.Path)
    file = path / TO_ENBID_FILENAME
    points = np.asarray(data)
    assert (np.loadtxt(file, delimiter=' ') == points-np.average(points, axis=0)).all()


if __name__ == '__main__':
    pass
