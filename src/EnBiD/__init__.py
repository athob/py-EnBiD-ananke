#!/usr/bin/env python
"""
Docstring
"""
import os
import pathlib
import subprocess
import tempfile
import numpy as np
import pandas as pd

from .constants import ENBID, ENBID_PARAMFILE_TEMPLATE

__all__ = ['enbid']

TEMP_DIR = tempfile.TemporaryDirectory()
POS = 'pos'
VEL = 'vel'
TO_ENBID_FILENAME = 'to_enbid'
ENBID_PARAMFILE = 'enbid_paramfile'
USEDVALUES_SUFFIX = '_enbid-usedvalues'
SNAPSHOT_FILEBASE = 'SnapshotFileBase'
ENBID_OUT_EXT = 'est'

USEDVALUES = '{}{}'.format(ENBID_PARAMFILE, USEDVALUES_SUFFIX)


def make_path_of_name(name=None):
    if name is None:
        raise TypeError  # TODO https://pypi.org/project/temppathlib/
    else:
        path = pathlib.Path(name)
        path.mkdir(parents=True, exist_ok=True)
    return path


def write_for_enbid(points, name=None):
    """
    Writes the input files for kernel density estimation (to calculate smoothing metric)
    """
    points = np.asarray(points)
    assert points.ndim == 2 and points.shape[-1] == 3, 'Array-like input must be of shape (X, 3)'
    path = make_path_of_name(name)
    np.savetxt(path / TO_ENBID_FILENAME, points, delimiter=' ')
    return path


def run_enbid(name=None, ngb=64):
    """
    Run package enbid using input files in name
    """
    path = make_path_of_name(name)
    with open(path / ENBID_PARAMFILE, 'w') as f:
        f.write(ENBID_PARAMFILE_TEMPLATE.substitute(fname=TO_ENBID_FILENAME, ngb=ngb))
    subprocess.call([ENBID, ENBID_PARAMFILE], cwd=path)
    return path


def return_enbid(name=None):
    """
    Nothing
    """
    path = make_path_of_name(name)
    usedvals = pd.read_table(path / USEDVALUES, header=None, delim_whitespace=True,
                             index_col=0).T.reset_index(drop=True).to_dict('records')[0]
    rho = np.loadtxt(path / '{}{}.{}'.format(TO_ENBID_FILENAME, usedvals[SNAPSHOT_FILEBASE], ENBID_OUT_EXT))
    return rho


def enbid(*args, **kwargs):
    points = args[0]
    name = kwargs.get('name', None)
    return return_enbid(run_enbid(write_for_enbid(points, name=name)))


if __name__ == '__main__':
    pass
