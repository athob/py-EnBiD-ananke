#!/usr/bin/env python
import pathlib

from ..enbid_ananke import CONSTANTS, run_enbid
from .utils import in_tmp_wd, make_enbid_test_exec, list_stdout


@in_tmp_wd
def test_run_enbid():
    CONSTANTS.enbid = pathlib.Path("./enbid_tester").absolute()
    enbid_exec = make_enbid_test_exec()
    with list_stdout() as L:
        run_enbid(name='test', verbose=True)
    assert CONSTANTS.enbid_paramfile in L


# TODO add tests for run_enbids kwargs


if __name__ == '__main__':
    pass
