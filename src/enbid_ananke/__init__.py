#!/usr/bin/env python
"""
enbid_ananke
======

Provides a set of utilities to run the kernel density estimator EnBiD
(`Sharma & Steinmetz 2011 <http://ascl.net/1109.012>`).

How to use
----------

EnBiD comes with the function enbid, please refer to its documentation
for further help.
"""
from typing import Any, Optional, Union, Tuple, Dict
from numpy.typing import ArrayLike, NDArray
import pathlib
import warnings
import hashlib
import numpy as np
import pandas as pd
from sklearn import neighbors as nghb

from .__metadata__ import *
from ._constants import *
from ._templates import *
from ._defaults import *
from .utils import execute

__all__ = ['enbid']


def __make_path_of_name(name : Optional[Union[str, pathlib.Path]] = None) -> pathlib.Path:
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


def write_for_enbid(points: ArrayLike, name : Optional[Union[str, pathlib.Path]] = None,
                    caching : bool = False) -> pathlib.Path:
    """
        Writes the input files for EnBiD given the input particles 3D
        coordinates.

        Call signature::

            path = write_for_enbid(points, name=None, caching=False)
        
        Parameters
        ----------
        points : array_like
            Contains 3D coordinates of the input particles, must be of shape
            (N,3) for any given N integer.
        
        name : string
            Name of folder where to place EnBiD input files. Default to None.
        
        caching : bool
            If True, check if EnBiD input file already exists and ignore
            writing if it does. Default to False.
        
        Returns
        ----------
        path : pathlib.Path
            Path of folder where EnBiD input files are located.
    """
    path: pathlib.Path = __make_path_of_name(name)
    enbid_inputfile: pathlib.Path = path / DEFAULT_FOR_PARAMFILE[TTAGS.fname]
    enbid_inputhashfile: pathlib.Path = enbid_inputfile.with_suffix(f".{HASH_EXT}")
    points: NDArray = np.asarray(points)
    inputhash = bytes(hashlib.sha256(points).hexdigest(), HASH_ENCODING)
    if ((enbid_inputhashfile.read_bytes() != inputhash # proceed if hashes don't match,
         if (enbid_inputfile.exists() and              # only if enbid_inputfile exists,
             enbid_inputhashfile.exists())             # and enbid_inputhashfile exists,
         else True)                                    # otherwise proceed if both don't exist
        if caching else True):                         # -> proceed anyway if caching is False
        assert points.ndim == 2 and points.shape[-1] == 3, 'Array-like input must be of shape (X, 3)'
        # depreciating that warning
        # temp = np.max(np.abs(np.average(points, axis=0)/np.std(points, axis=0)))
        # if temp>1: warnings.warn("Input points may be not centered, which may cause EnBiD to run into a SegmentationFault")
        # center frame on most clustered structure using NN distances
        NN = nghb.NearestNeighbors(n_neighbors=2)
        NN.fit(points)
        NN_distances: NDArray = NN.kneighbors(points)[0][:,1]
        most_clustered_structure: NDArray = points[NN_distances < np.median(NN_distances)]
        most_clustered_structure_center: NDArray = np.average(most_clustered_structure, axis=0)
        #
        coordinates: NDArray = points - most_clustered_structure_center
        np.savetxt(enbid_inputfile, coordinates, delimiter=' ')
        enbid_inputhashfile.write_bytes(inputhash)
    return path


def run_enbid(name: Optional[Union[str, pathlib.Path]] = None, ngb: int = DEFAULT_NGB,
              verbose: bool = True, caching: bool = False, **kwargs: Dict[str, Any]) -> pathlib.Path:
    """
        Run EnBiD using input files in name.

        Call signature::

            path = run_enbid(name=None, ngb=64, verbose=True,
                             caching=False, **kwargs)
        
        Parameters
        ----------
        name : string
            Name of folder where EnBiD input files are located. Default to
            None.

        ngb : int
            Number of neighbouring particles EnBiD should consider in the
            smoothing for the density estimation. Default to {DEFAULT_NGB}.

        verbose : bool
            Verbose boolean flag to allow EnBiD to print what it's doing to
            stdout. Default to True.

        caching : bool
            If True, check if EnBiD paramfile and usedvalues files already
            exist, and ignore running if parameters from the previous run are
            the same. Default to False.
        
        spatial_scale : float
            Scaling between position and velocity space where the scaling goes
            as velocity = position/spatial_scale if spatial_scale is set
            strictly positive, or velocity = position/std(position) if
            spatial_scale is set to 0 (with std representing the standard
            deviation for each coordinate). Default to 1 - TODO currently not
            implemented.
        
        part_bounday : int
            Minimum number of particles which a node must contain to have a
            boundary correction applied to its surfaces during tree generation.
            Optimum choice should be whichever the higher between 7 or d+1
            where d is the dimensionality of the space considered.
            Default to 7.
        
        node_splitting_criterion : int (0, 1)
            Flag to allow for the node splitting to always split in priority
            the dimension with lowest Shannon entropy. If set to 0, the
            criteria splits each dimension alternately. Default to 1.
        
        cubic_cells : int (0, 1)
            Flag to allow the node splitting to use position or velocity
            subspaces rather than individual dimensions when generating cells.
            Only work for 3 & 6 dimensional spaces. Default to 0 - TODO
            currently not implemented.
        
        median_splitting_on : int (0, 1)
            Flag to allow for cell splitting to happen at the mean of data
            points when building the tree for faster estimates. Default to 0
            - TODO currently not implemented.
        
        type_of_smoothing : int (0, 1, 2, 3, 4, 5)
            Type of smoothing used:
                0) None
                1) FiEstAS
                2) Normal isotropic spherical kernel
                3) Adaptive metric spherical kernel
                4) Normal isotropic product form kernel
                5) Adaptive metric product form kernel
            Default to 3.
        
        vol_corr : int (0, 1)
            Flag to enable a correction that avoid underestimating density
            when the smoothing box extends outside the boundary. Default to 1.
        
        type_of_kernel : int (0, 1, 2, 3, 4, 5)
            Type of the kernel profile used:
                0) B-spline
                1) Top hat
                2) Bi-weight (1-x^2)^2
                3) Epanechikov
                4) Cloud in cell
                5) Triangular shaped cloud
            Default to 3.
        
        kernel_bias_correction : int (0, 1)
            Flag to enable corrections that displace central data points when
            computing densities, and reduce bias caused by irregularly
            distributed data. Default to 1.
        
        anisotropy_kernel : int (0, 1)
            Flag to enable the use of anisotropic kernels which can have both
            shear and rotation. Kerels become then rotated ellipsoids in the
            density computation. With it on, type_of_smoothing should be either
            2 or 3. Default to 0.
        
        anisotropy : float
            Minimum allowable minor to major axis ratio of the kernel smoothing
            lengths for computational management. Default to 0.
        
        ngb_a : int
            Number of neighbouring particles EnBiD should consider when
            computing the anisotropic kernel. Default to ngb.
        
        type_list_on : int (0, 1)
            Flag to extend the number of particle types on which EnBiD can
            run independent density estimations from the default 6 types of
            GADGET formated data. Default to 0 - TODO currently not
            implemented.
        
        periodic_boundary_on : int (0, 1)
            Flag to allow periodic boundary conditions. Default to 0 - TODO
            currently not implemented.
        
        Returns
        ----------
        path : pathlib.Path
            Path of folder where EnBiD output files are located.
    """
    path: pathlib.Path = __make_path_of_name(name)
    kwargs[TTAGS.des_num_ngb] = ngb
    kwargs[TTAGS.des_num_ngb_a] = kwargs.pop('ngb_a', ngb)
    paramfile_text: str = ENBID_PARAMFILE_TEMPLATE.substitute(DEFAULT_FOR_PARAMFILE, **kwargs)
    paramfile: pathlib.Path = path / CONSTANTS.enbid_paramfile
    usedvalfile: pathlib.Path = path / CONSTANTS.usedvalues
    if ((paramfile.read_text() != paramfile_text # proceed if paramfile_text is not in paramfile,
         if (paramfile.exists() and              # only if paramfile exist,
             usedvalfile.exists())               # and usedvalfile exists,
         else True)                              # otherwise proceed if both don't exist
        if caching else True):                   # -> proceed anyway if caching is False
        paramfile.write_text(paramfile_text)
        execute([CONSTANTS.enbid, CONSTANTS.enbid_paramfile], verbose=verbose, cwd=path)
    return path

run_enbid.__doc__ = run_enbid.__doc__.format(DEFAULT_NGB=DEFAULT_NGB)


def return_enbid(name: Optional[Union[str, pathlib.Path]] = None) -> NDArray:
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
    path: pathlib.Path = __make_path_of_name(name)
    usedvals = pd.read_table(path / CONSTANTS.usedvalues, header=None, delim_whitespace=True,
                             index_col=0).T.reset_index(drop=True).to_dict('records')[0]
    rho: NDArray = np.loadtxt(path / f"{DEFAULT_FOR_PARAMFILE[TTAGS.fname]}{usedvals[SNAPSHOT_FILEBASE]}.{ENBID_OUT_EXT}")
    return rho


def enbid(*args: Tuple[Any], **kwargs: Dict[str, Any]) -> NDArray:
    """
        Returns kernel density estimates given a set of particle 3D coordinates.

        Call signature::

            rho = enbid(points, name=None, **kwargs)
        
        Parameters
        ----------
        points : array_like
            Contains 3D coordinates of the input particles, must be of shape
            (N,3) for any given N integer.

        name : string
            Name of folder where to save the input/output files for the EnBiD
            estimator. Default to None.
        
        caching : bool
            Only to be used with a given folder under argument name. If True,
            check if EnBiD had already been used to produce the kernel density
            estimates. If it hasn't, compute the estimates, otherwise, load
            the existing data that had previously been cached. Default to
            False.
        
        **kwargs : dict
            Refer to function run_enbid documentation for additional keyword
            arguments.
        
        Returns
        ----------
        rho : array_like
            Array representing kernel density estimates for the input particles
    """
    points = args[0]
    name = kwargs.pop('name', None)
    caching = False if name is None else kwargs.pop('caching', False)
    return return_enbid(run_enbid(write_for_enbid(points, name=name, caching=caching), caching=caching, **kwargs))


if __name__ == '__main__':
    raise NotImplementedError()
