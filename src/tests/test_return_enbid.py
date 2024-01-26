#!/usr/bin/env python
import random

import numpy as np

from ..EnBiD_ananke import return_enbid
from .utils import in_tmp_wd, simulate_enbid_output


@in_tmp_wd
def test_return_enbid():
    name = 'test'
    tag = '_d3n64'
    values = [random.randrange(1000000)/1000 for n in range(20)]
    simulate_enbid_output(name, tag, values)
    rho = return_enbid(name)
    np.testing.assert_array_almost_equal_nulp(rho, values)


if __name__ == '__main__':
    pass
