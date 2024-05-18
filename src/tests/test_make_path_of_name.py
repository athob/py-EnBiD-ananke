#!/usr/bin/env python
import pytest
import pathlib

from ..EnBiD_ananke import __make_path_of_name
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
