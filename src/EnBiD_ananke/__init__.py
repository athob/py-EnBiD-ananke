#!/usr/bin/env python
"""
EnBiD
======

Provides a set of utilities to run the kernel density estimator EnBiD
(`Sharma & Steinmetz 2011 <http://ascl.net/1109.012>`).

How to use
----------

EnBiD comes with the function enbid, please refer to its documentation
for further help.
"""
import pathlib
import subprocess
import warnings
import numpy as np
import pandas as pd

from .__metadata__ import *
from .constants import *

__all__ = ['enbid']


def make_path_of_name(name=None):
    """
        Generate the folders structure representing a given name as a path,
        or generate a temporary one.

        Call signature::

            path = run_enbid(name=None)
        
        Parameters
        ----------
        name : string
            Path representing a folders structure. Default to None.
        
        Returns
        ----------
        path : pathlib.Path
            Path corresponding to given name, or to new temporary one.
    """
    if name is None:
        raise NotImplementedError("name is None")  # TODO https://pypi.org/project/temppathlib/
    else:
        path = pathlib.Path(name)
        path.mkdir(parents=True, exist_ok=True)
    return path


def write_for_enbid(points, name=None):
    """
        Writes the input files for EnBiD given the input particles 3D
        coordinates.

        Call signature::

            path = write_for_enbid(points, name=None)
        
        Parameters
        ----------
        points : array_like
            Contains 3D coordinates of the input particles, must be of shape
            (N,3) for any given N integer.
        
        name : string
            Name of folder where to place EnBiD input files. Default to None.
        
        Returns
        ----------
        path : pathlib.Path
            Path of folder where EnBiD input files are located.
    """
    points = np.asarray(points)
    assert points.ndim == 2 and points.shape[-1] == 3, 'Array-like input must be of shape (X, 3)'
    temp = np.max(np.abs(np.average(points, axis=0)/np.std(points, axis=0)))
    if temp>1: warnings.warn("Input points may be not centered, which may cause EnBiD to run into a SegmentationFault")
    path = make_path_of_name(name)
    np.savetxt(path / TO_ENBID_FILENAME, points, delimiter=' ')
    return path


def run_enbid(name=None, ngb=64):
    """
        Run EnBiD using input files in name.

        Call signature::

            path = run_enbid(name=None, ngb=64)
        
        Parameters
        ----------
        name : string
            Name of folder where EnBiD input files are located. Default to
            None.

        ngb : int
            Number of neighbouring particles EnBiD should consider in the
            kernel density estimation. Default to 64.
        
        Returns
        ----------
        path : pathlib.Path
            Path of folder where EnBiD output files are located.
    """
    path = make_path_of_name(name)
    with open(path / ENBID_PARAMFILE, 'w') as f:
        f.write(ENBID_PARAMFILE_TEMPLATE.substitute(fname=TO_ENBID_FILENAME, ngb=ngb))
    subprocess.call([ENBID, ENBID_PARAMFILE], cwd=path)
    return path


def return_enbid(name=None):
    """
        Read EnBiD output file and returns the associated kernel density
        estimates after running the EnBiD estimator.

        Call signature::

            rho = return_enbid(name=None)
        
        Parameters
        ----------
        name : string
            Name of folder where EnBiD saved its output files. Default to None.
        
        Returns
        ----------
        rho : array_like
            Array representing the kernel density estimates output by EnBiD
    """
    path = make_path_of_name(name)
    usedvals = pd.read_table(path / USEDVALUES, header=None, delim_whitespace=True,
                             index_col=0).T.reset_index(drop=True).to_dict('records')[0]
    rho = np.loadtxt(path / '{}{}.{}'.format(TO_ENBID_FILENAME, usedvals[SNAPSHOT_FILEBASE], ENBID_OUT_EXT))
    return rho


def enbid(*args, **kwargs):
    """
        Returns kernel density estimates given a set of particle 3D coordinates.

        Call signature::

            rho = enbid(points, name=None, ngb=64)
        
        Parameters
        ----------
        points : array_like
            Contains 3D coordinates of the input particles, must be of shape
            (N,3) for any given N integer.

        name : string
            Name of folder where to save the input/output files for the EnBiD
            estimator. Default to None.

        ngb : int
            Number of neighbouring particles EnBiD should consider in the
            kernel density estimation. Default to 64.
        
        Returns
        ----------
        rho : array_like
            Array representing kernel density estimates for the input particles
    """
    points = args[0]
    name = kwargs.get('name', None)
    ngb = kwargs.get('ngb', 64)
    return return_enbid(run_enbid(write_for_enbid(points, name=name), ngb=ngb))


if __name__ == '__main__':
    pass
