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
"""
enbid_ananke
============

Provides a set of utilities to run the kernel density estimator EnBiD
(`Sharma & Steinmetz 2011 <http://ascl.net/1109.012>`).

How to use
----------

enbid_ananke comes with the function enbid, please refer to its documentation
for further help.
"""
from typing import Any, Optional, Union, Tuple, Dict
from numpy.typing import ArrayLike, NDArray
import pathlib
import warnings
import hashlib
import struct
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

            path = __make_path_of_name(name=None)
        
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


def write_gadget_file(filename: pathlib.Path, pos: NDArray, mass: NDArray, vel: Optional[NDArray] = None,
                      boxsize: float = 0.0, time: float = 0.0, redshift: float = 0.0,
                      omega0: float = 0.0, omegalambda: float = 0.0, hubble: float = 0.7,
                      particle_type: int = 1) -> None:
    """
    Write a GADGET-1 format snapshot file to serve as input for EnBiD (3D or 6D).

    Parameters
    ----------
    filename : pathlib.Path
        Output file path.
    pos : ndarray, shape (N, 3)
        Particle positions (float32).
    mass : ndarray, shape (N,)
        Particle masses (float32).
    vel : ndarray, shape (N, 3), optional
        Particle velocities. If None, zero velocities are written.
    boxsize : float, optional
        Size of periodic box.
    time, redshift, omega0, omegalambda, hubble : float, optional
        Cosmological parameters (ignored by EnBiD but part of header).
    particle_type : int, optional
        Particle type index (0-5).
    """
    N = pos.shape[0]
    if mass.shape[0] != N:
        raise ValueError("pos and mass must have same number of particles")

    # Ensure correct data types
    pos = np.asarray(pos, dtype=np.float32)
    mass = np.asarray(mass, dtype=np.float32)
    # vel = np.zeros((N, 3), dtype=np.float32)      # dummy velocities
    if vel is None:
        vel = np.zeros((N, 3), dtype=np.float32)      # dummy velocities
    else:
        vel = np.asarray(vel, dtype=np.float32)
        if vel.shape[0] != N or vel.shape[1] != 3:
            raise ValueError("vel must have shape (N, 3)")
    ids = np.arange(1, N+1, dtype=np.int32)       # dummy IDs (1-based)

    # Build header (256 bytes)
    npart = np.zeros(6, dtype=np.int32)
    npart[particle_type] = N
    massarr = np.zeros(6, dtype=np.float64)
    nall = npart.copy()

    # Build header without padding first, then pad to 256 bytes
    header_data = struct.pack(
        '<6i6d2d2i6i2i4d3i',
        npart[0], npart[1], npart[2], npart[3], npart[4], npart[5],
        massarr[0], massarr[1], massarr[2], massarr[3], massarr[4], massarr[5],
        time, redshift,
        0, 0,                              # flag_sfr, flag_feedback
        nall[0], nall[1], nall[2], nall[3], nall[4], nall[5],
        0, 1,                              # flag_cooling, num_files
        boxsize, omega0, omegalambda, hubble,
        0, 0, 1                            # flag_id, flag_dim, flag_density
    )
    # Pad to exactly 256 bytes
    padding_len = 256 - len(header_data)
    if padding_len < 0:
        raise RuntimeError("Header exceeds 256 bytes")
    header_data += b'\x00' * padding_len

    def write_record(f, data):
        f.write(struct.pack('<i', len(data)))
        f.write(data)
        f.write(struct.pack('<i', len(data)))

    with open(filename, 'wb') as f:
        write_record(f, header_data)
        write_record(f, pos.ravel().tobytes())
        write_record(f, vel.ravel().tobytes())
        write_record(f, ids.tobytes())
        write_record(f, mass.ravel().tobytes())


def write_for_enbid(points: ArrayLike, 
                    velocities: Optional[ArrayLike] = None,
                    mass: Optional[ArrayLike] = None,
                    name: Optional[Union[str, pathlib.Path]] = None,
                    caching: bool = False) -> pathlib.Path:
    """
        Writes the input files for EnBiD from 3D positions (and optional
        3D velocities). If velocities are given, the combined input represents
        6D phase-space data. The position frame is automatically centred on
        the most clustered structure to improve numerical stability;
        velocities are left unchanged.

        Call signature::

            path = write_for_enbid(points, velocities=None, mass=None,
                                   name=None, caching=False)
        
        Parameters
        ----------
        points : array_like
            Contains 3D coordinates of the input particles, must be of shape
            (N,3) for any given N integer.

        velocities : array_like, optional
            Particle velocities, shape (N, 3). If provided, EnBiD will run in 6D
            phase-space mode.

        mass : array_like, optional
            Contains the mass of each particle. Must be a 1D array of length N.
            If provided, a GADGET binary input file is written and EnBiD will
            compute mass-weighted densities. If None (default), an ASCII file
            is written and unit masses are assumed.

        name : string, optional
            Name of folder where to place EnBiD input files. Default to None.
        
        caching : bool, optional
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
    mass_arr: Optional[NDArray] = np.asarray(mass) if mass is not None else None
    vel_arr: Optional[NDArray] = np.asarray(velocities) if velocities is not None else None
    # Validate shapes
    if vel_arr is not None:
        assert points.ndim == 2 and points.shape[-1] == 3, 'Points must be (N,3)'
        assert vel_arr.ndim == 2 and vel_arr.shape[-1] == 3, 'Velocities must be (N,3)'
        assert vel_arr.shape[0] == points.shape[0], 'Points and velocities must have same N'
    else:
        assert points.ndim == 2 and points.shape[-1] == 3, 'Points must be (N,3)'

    if mass_arr is not None:
        assert mass_arr.ndim == 1 and mass_arr.shape[0] == points.shape[0], 'Mass array length mismatch'
    # Compute hash including mass and/or velocities  if present
    hash_input = points.tobytes()
    if vel_arr is not None:
        hash_input += vel_arr.tobytes()
    if mass_arr is not None:
        hash_input += mass_arr.tobytes()
    inputhash = bytes(hashlib.sha256(hash_input).hexdigest(), HASH_ENCODING)
    # Check if we need to write the file
    if ((enbid_inputhashfile.read_bytes() != inputhash # proceed if hashes don't match,
         if (enbid_inputfile.exists() and              # only if enbid_inputfile exists,
             enbid_inputhashfile.exists())             # and enbid_inputhashfile exists,
         else True)                                    # otherwise proceed if both don't exist
        if caching else True):                         # -> proceed anyway if caching is False
        assert points.ndim == 2 and points.shape[-1] == 3, 'Array-like input must be of shape (X, 3)'
        if mass_arr is not None:
            assert mass_arr.ndim == 1 and mass_arr.shape[0] == points.shape[0], 'mass must be 1D array with same length as points'
        if points.shape[0]:
            # center frame on most clustered structure using NN distances
            NN = nghb.NearestNeighbors(n_neighbors=2)
            NN.fit(points)
            NN_distances: NDArray = NN.kneighbors(points)[0][:,1]
            most_clustered_structure: NDArray = points[NN_distances < np.median(NN_distances)]
            most_clustered_structure_center: NDArray = np.average(most_clustered_structure, axis=0)
            #
            coordinates: NDArray = points - most_clustered_structure_center
        else:
            coordinates: NDArray = points

        if mass_arr is None:
            # ASCII format: write positions (and velocities if present)
            if vel_arr is not None:
                # 6 columns
                combined = np.column_stack((coordinates, vel_arr))
                np.savetxt(enbid_inputfile, combined, delimiter=' ')
            else:
                np.savetxt(enbid_inputfile, coordinates, delimiter=' ')
        else:
            # GADGET binary format
            write_gadget_file(enbid_inputfile, coordinates, mass_arr,
                              vel=vel_arr if vel_arr is not None else None)

        enbid_inputhashfile.write_bytes(inputhash)
    
    return path


def run_enbid(points: ArrayLike,
              velocities: Optional[ArrayLike] = None, mass: Optional[ArrayLike] = None,
              name: Optional[Union[str, pathlib.Path]] = None, ngb: int = DEFAULT_NGB,
              verbose: bool = True, caching: bool = False, **kwargs: Dict[str, Any]) -> pathlib.Path:
    """
        Run the EnBiD kernel density estimator on the supplied particle data.
        The appropriate pre-compiled EnBiD binary (3D or 6D) is selected
        automatically based on whether ``velocities`` are provided.

        Call signature::

            path = run_enbid(points, velocities=None, mass=None,
                             name=None, ngb=64, verbose=True,
                             caching=False, **kwargs)
        
        Parameters
        ----------
        points : array_like
            Contains 3D coordinates of the input particles, must be of shape
            (N,3) for any given N integer.

        velocities : array_like, optional
            Particle velocities, shape (N, 3). If provided, EnBiD runs in 6D mode.

        mass : array_like, optional
            Contains the mass of each particle. Must be a 1D array of length N.
            If provided, a GADGET binary input file is written and EnBiD will
            compute mass-weighted densities. If None (default), an ASCII file
            is written and unit masses are assumed.

        name : string, optional
            Name of folder where EnBiD input files are located. Default to
            None.

        ngb : int, optional
            Number of neighbouring particles EnBiD should consider in the
            smoothing for the density estimation. Default to {DEFAULT_NGB}.

        verbose : bool, optional
            Verbose boolean flag to allow EnBiD to print what it's doing to
            stdout. Default to True.

        caching : bool, optional
            If True, the input data is hashed and compared to a cached hash.
            If the data (points, velocities, masses) are unchanged, the
            existing parameter file and density estimates are reused.
            Default to False.
        
        spatial_scale : float, optional
            Scaling between position and velocity space where the scaling goes
            as velocity = position/spatial_scale if spatial_scale is set
            strictly positive, or velocity = position/std(position) if
            spatial_scale is set to 0 (with std representing the standard
            deviation for each coordinate). Default to 1 - TODO currently not
            implemented.
        
        part_boundary : int, optional
            Minimum number of particles which a node must contain to have a
            boundary correction applied to its surfaces during tree generation.
            Optimum choice should be the larger of 7 or d+1, where d is the
            dimensionality of the space considered. Default to 7.
        
        node_splitting_criterion : int (0, 1), optional
            Flag to allow for the node splitting to always split in priority
            the dimension with lowest Shannon entropy. If set to 0, the
            criteria splits each dimension alternately. Default to 1.
        
        cubic_cells : int (0, 1), optional
            Flag to allow the node splitting to use position or velocity
            subspaces rather than individual dimensions when generating cells.
            Only work for 3 & 6 dimensional spaces. Default to 0 - TODO
            currently not implemented.
        
        median_splitting_on : int (0, 1), optional
            Flag to allow for cell splitting to happen at the mean of data
            points when building the tree for faster estimates. Default to 1
            (requires EnBiD compiled with -DMEDIAN TODO).
        
        type_of_smoothing : int (0, 1, 2, 3, 4, 5), optional
            Type of smoothing used:
                0) None
                1) FiEstAS
                2) Normal isotropic spherical kernel
                3) Adaptive metric spherical kernel
                4) Normal isotropic product form kernel
                5) Adaptive metric product form kernel
            Default to 3.
        
        vol_corr : int (0, 1), optional
            Flag to enable a correction that avoid underestimating density
            when the smoothing box extends outside the boundary. Default to 1.
        
        type_of_kernel : int (0, 1, 2, 3, 4, 5), optional
            Type of the kernel profile used:
                0) B-spline
                1) Top hat
                2) Bi-weight (1-x^2)^2
                3) Epanechikov
                4) Cloud in cell
                5) Triangular shaped cloud
            Default to 3.
        
        kernel_bias_correction : int (0, 1), optional
            Flag to enable corrections that displace central data points when
            computing densities, and reduce bias caused by irregularly
            distributed data. Default to 1.
        
        anisotropy_kernel : int (0, 1), optional
            Flag to enable the use of anisotropic kernels which can have both
            shear and rotation. Kerels become then rotated ellipsoids in the
            density computation. With it on, type_of_smoothing should be either
            2 or 3. Default to 0.
        
        anisotropy : float, optional
            Minimum allowable minor to major axis ratio of the kernel smoothing
            lengths for computational management. Default to 0.
        
        ngb_a : int, optional
            Number of neighbouring particles EnBiD should consider when
            computing the anisotropic kernel. Default to ngb.
        
        type_list_on : int (0, 1), optional
            Flag to extend the number of particle types on which EnBiD can
            run independent density estimations from the default 6 types of
            GADGET formated data. Default to 0 - TODO currently not
            implemented.
        
        periodic_boundary_on : int (0, 1), optional
            Flag to allow periodic boundary conditions. Default to 0 - TODO
            currently not implemented.
        
        Returns
        ----------
        path : pathlib.Path
            Path of folder where EnBiD output files are located.
    """
    # Determine ICFormat based on whether mass is provided
    ic_format = 1 if mass is not None else 0
    kwargs[TTAGS.ic_format] = ic_format
    # Determine dimension tag for output file suffix
    dim_tag = 'd6' if velocities is not None else 'd3'
    kwargs[TTAGS.snapshot_filebase] = f"_{dim_tag}n{ngb}"
    # Write input files
    path = write_for_enbid(points, velocities=velocities, mass=mass, name=name, caching=caching)
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
        # Choose the right executable
        enbid_exec = CONSTANTS.enbid6d if velocities is not None else CONSTANTS.enbid3d
        execute([enbid_exec, CONSTANTS.enbid_paramfile], verbose=verbose, cwd=path)
    return path

run_enbid.__doc__ = run_enbid.__doc__.format(DEFAULT_NGB=DEFAULT_NGB)


def read_enbid_binary(filename: pathlib.Path) -> NDArray:
    """
    Read a binary EnBiD density file (GADGET-style output).

    The file contains a 256-byte header followed by a block of
    single-precision floats (density for each particle).
    Each record is preceded and followed by a 4-byte integer
    indicating the block size (Fortran unformatted).

    Parameters
    ----------
    filename : pathlib.Path
        Path to the .est file.

    Returns
    -------
    density : ndarray
        Array of density values (float32).
    """
    with open(filename, 'rb') as f:
        # Read and skip header block
        blklen_data = f.read(4)
        if len(blklen_data) != 4:
            raise IOError("Failed to read block size for header")
        blklen = struct.unpack('<i', blklen_data)[0]
        if blklen != 256:
            raise ValueError(f"Expected header size 256, got {blklen}")
        f.read(256)  # header
        f.read(4)    # trailing block size

        # Read density block
        blklen_data = f.read(4)
        if len(blklen_data) != 4:
            raise IOError("Failed to read block size for density")
        blklen = struct.unpack('<i', blklen_data)[0]
        n_floats = blklen // 4
        density_bytes = f.read(blklen)
        density = np.frombuffer(density_bytes, dtype=np.float32, count=n_floats)
    return density


def return_enbid(name: Optional[Union[str, pathlib.Path]] = None) -> NDArray:
    """
        Read EnBiD output file and returns the associated kernel density
        estimates after running the EnBiD estimator.

        Automatically detects whether the output is ASCII or binary
        based on the ICFormat used in the run.

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
    usedvals = pd.read_table(path / CONSTANTS.usedvalues, header=None, sep="\s+",
                             index_col=0).T.reset_index(drop=True).to_dict('records')[0]
    output_file = path / f"{DEFAULT_FOR_PARAMFILE[TTAGS.fname]}{usedvals[SNAPSHOT_FILEBASE]}.{ENBID_OUT_EXT}"

    # Check ICFormat used in this run
    ic_format = int(usedvals.get('ICFormat', 0))
    if ic_format == 1:
        # Binary GADGET output
        rho = read_enbid_binary(output_file)
    else:
        # ASCII output (default)
        rho = np.loadtxt(output_file)
    return rho


def enbid(points: ArrayLike,
          velocities: Optional[ArrayLike] = None,
          mass: Optional[ArrayLike] = None,
          **kwargs: Dict[str, Any]) -> NDArray:
    """
        Returns kernel density estimates for a set of particles.

        If only 3D positions are given, the result is a 3D spatial density.
        If 3D velocities are also provided, the estimate becomes a 6D
        phase-space density.  When a `mass` array is given, the densities are
        mass-weighted (mass density); otherwise they are number densities.

        Call signature::

            rho = enbid(points, velocities=None, mass=None, name=None, **kwargs)
        
        Parameters
        ----------
        points : array_like
            Contains 3D coordinates of the input particles, must be of shape
            (N,3) for any given N integer.

        velocities : array_like, optional
            Particle velocities, shape (N, 3). If provided, EnBiD runs in 6D
            phase-space mode.

        mass : array_like, optional
            Contains the mass of each particle. Must be a 1D array of length N.
            If provided, a GADGET binary input file is written and EnBiD will
            compute mass-weighted densities (i.e., mass density). If None (default),
            an ASCII file is written and unit masses are assumed (number density).

        name : string, optional
            Name of folder where to save the input/output files for the EnBiD
            estimator. Default to None.
        
        caching : bool, optional
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
            Array of density values.  Units: mass density if `mass` is given,
            number density otherwise.
    """
    # points = args[0]
    name = kwargs.pop('name', None)
    caching = False if name is None else kwargs.pop('caching', False)
    return return_enbid(run_enbid(points, velocities=velocities, mass=mass, name=name, caching=caching, **kwargs))


if __name__ == '__main__':
    raise NotImplementedError()
