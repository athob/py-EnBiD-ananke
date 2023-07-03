#!/usr/bin/env python
"""
Contains the EnBiD module constants.
"""
import pathlib
import tempfile
from string import Template

__all__ = ['NAME', 'LOG_DIR', 'SRC_DIR', 'ENBID2', 'ENBID_URL', 'ENBID', 'TO_ENBID_FILENAME', 'ENBID_PARAMFILE', 'USEDVALUES', 'SNAPSHOT_FILEBASE', 'ENBID_OUT_EXT', 'DEFAULT_NGB', 'ENBID_PARAMFILE_TEMPLATE', 'DEFAULT_FOR_PARAMFILE']

NAME = 'EnBiD_ananke'
ENBID2 = 'Enbid-2.0'
ENBID_URL = 'https://sourceforge.net/projects/enbid/files/latest/download'
ENBID_EXEC = 'Enbid'
LOG_DIR = 'log'
SRC_DIR = 'src'

TO_ENBID_FILENAME = 'to_enbid'
ENBID_PARAMFILE = 'enbid_paramfile'
USEDVALUES_SUFFIX = '_enbid-usedvalues'
SNAPSHOT_FILEBASE = 'SnapshotFileBase'
ENBID_OUT_EXT = 'est'
DEFAULT_NGB = 64

ENBID_PARAMFILE_TEMPLATE = Template("""%  Input and Output
InitCondFile     ${fname}

%-------------------------------------------------------
ICFormat                  0     % O)ASCII 1)Gadget 2)User defined
SnapshotFileBase        _d3n${des_num_ngb}

%-------------------------------------------------------
% Tree related options
SpatialScale            ${spatial_scale}   % x->x/SpatialScale and v->v
PartBoundary            ${part_boundary}   % Min particles in a node to do boundary correction
NodeSplittingCriterion  ${node_splitting_criterion}   % 0)Alternate 1) Min Entropy
CubicCells              ${cubic_cells}   % use 1 in spherically symmetric systems
MedianSplittingOn       ${median_splitting_on}

%--------------------------------------------------------
% Smoothing options  AM=adaptive metric Ker=Kernel Sp=Spherical Pr=Product
% 0) None 1)FiEstAS 2)Ker Sp Normal 3)Ker Sp AM 4)KerPr Normal 5)KerPr AM
TypeOfSmoothing      ${type_of_smoothing}
DesNumNgb            ${des_num_ngb}   % 2-10 for Fiestas and 25-100 for Kernel
VolCorr              ${vol_corr}    %  0) Disbale 1) Enable

%--------------------------------------------------------
% Kernel smoothing  related options
% 0) B-Spline 1)top hat 2)Bi_weight (1-x^2)^2 3)Epanechikov 4)CIC 5)TSC
TypeOfKernel           ${type_of_kernel}
KernelBiasCorrection   ${kernel_bias_correction}    % 0)none 1)shift central particle
AnisotropicKernel      ${anisotropy_kernel}    % 0) Isotropic 1) Anisotropic
Anisotropy             ${anisotropy}    % fix minimum c/a minor/major axis ratio
DesNumNgbA             ${des_num_ngb_a}   % Neighbors for cal covar metric for Anisotropic Ker
%--------------------------------------------------------
% other miscellaneous option
TypeListOn        ${type_list_on}
PeriodicBoundaryOn ${periodic_boundary_on}
%--------------------------------------------------------""")
DEFAULT_FOR_PARAMFILE = {
    'fname': TO_ENBID_FILENAME,
    'spatial_scale': 1.0,
    'part_boundary': 7,
    'node_splitting_criterion': 1,
    'cubic_cells': 0,
    'median_splitting_on': 1,
    'type_of_smoothing': 3,
    'vol_corr': 1,
    'type_of_kernel': 3,
    'kernel_bias_correction': 1,
    'anisotropy_kernel': 0,
    'anisotropy': 0,
    'type_list_on': 0,
    'periodic_boundary_on': 0
}


TEMP_DIR = tempfile.TemporaryDirectory()

ENBID_CPP = pathlib.Path(__file__).resolve().parent / ENBID2
ENBID = ENBID_CPP / ENBID_EXEC

USEDVALUES = f"{ENBID_PARAMFILE}{USEDVALUES_SUFFIX}"

