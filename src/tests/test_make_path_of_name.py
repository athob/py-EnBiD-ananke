#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2022  Adrien CR Thob
#
# This file is part of the py-EnBiD-ananke project,
# <https://github.com/athob/py-EnBiD-ananke>,  which is licensed
# under the GNU General Public License v2.0 (GPL-2.0).
# 
# The full copyright notice, including terms governing use, modification,
# and redistribution, is contained in the files LICENSE and COPYRIGHT,
# which can be found at the root of the source code distribution tree:
# - LICENSE <https://github.com/athob/py-EnBiD-ananke/blob/main/LICENSE>
# - COPYRIGHT <https://github.com/athob/py-EnBiD-ananke/blob/main/COPYRIGHT>
#
import pytest
import pathlib

from ..enbid_ananke import __make_path_of_name
from .utils import in_tmp_wd


def test_name_is_none():
    with pytest.raises(NotImplementedError):
        __make_path_of_name()

@in_tmp_wd
def test_name_is_not_none():
    name = 'test1234/test5678'
    path = __make_path_of_name(name=name)
    assert isinstance(path, pathlib.Path)
    assert path.exists()


if __name__ == '__main__':
    pass
