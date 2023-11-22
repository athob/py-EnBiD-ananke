#!/usr/bin/env python
"""
Contains the EnBiD module constants.
"""
import pathlib
import tempfile
from string import Template
from dataclasses import dataclass

from .utils import Singleton

__all__ = ['NAME', 'LOG_DIR', 'SRC_DIR', 'ENBID2', 'ENBID_URL', 'CONSTANTS', 'TO_ENBID_FILENAME', 'SNAPSHOT_FILEBASE', 'ENBID_OUT_EXT', 'DEFAULT_NGB', 'TTAGS', 'ENBID_PARAMFILE_TEMPLATE', 'DEFAULT_FOR_PARAMFILE']

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

@dataclass(frozen=True)
class Constants(metaclass=Singleton):
    fname: str                    = 'fname'
    des_num_ngb: str              = 'des_num_ngb'
    spatial_scale: str            = 'spatial_scale'
    part_boundary: str            = 'part_boundary'
    node_splitting_criterion: str = 'node_splitting_criterion'
    cubic_cells: str              = 'cubic_cells'
    median_splitting_on: str      = 'median_splitting_on'
    type_of_smoothing: str        = 'type_of_smoothing'
    vol_corr: str                 = 'vol_corr'
    type_of_kernel: str           = 'type_of_kernel'
    kernel_bias_correction: str   = 'kernel_bias_correction'
    anisotropy_kernel: str        = 'anisotropy_kernel'
    anisotropy: str               = 'anisotropy'
    des_num_ngb_a: str            = 'des_num_ngb_a'
    type_list_on: str             = 'type_list_on'
    periodic_boundary_on: str     = 'periodic_boundary_on'

TTAGS = Constants()

ENBID_PARAMFILE_TEMPLATE = Template(f"""%  Input and Output
InitCondFile     ${{{TTAGS.fname}}}

%-------------------------------------------------------
ICFormat                  0     % O)ASCII 1)Gadget 2)User defined
SnapshotFileBase        _d3n${{{TTAGS.des_num_ngb}}}

%-------------------------------------------------------
% Tree related options
SpatialScale            ${{{TTAGS.spatial_scale}}}   % x->x/SpatialScale and v->v
PartBoundary            ${{{TTAGS.part_boundary}}}   % Min particles in a node to do boundary correction
NodeSplittingCriterion  ${{{TTAGS.node_splitting_criterion}}}   % 0)Alternate 1) Min Entropy
CubicCells              ${{{TTAGS.cubic_cells}}}   % use 1 in spherically symmetric systems
MedianSplittingOn       ${{{TTAGS.median_splitting_on}}}

%--------------------------------------------------------
% Smoothing options  AM=adaptive metric Ker=Kernel Sp=Spherical Pr=Product
% 0) None 1)FiEstAS 2)Ker Sp Normal 3)Ker Sp AM 4)KerPr Normal 5)KerPr AM
TypeOfSmoothing      ${{{TTAGS.type_of_smoothing}}}
DesNumNgb            ${{{TTAGS.des_num_ngb}}}   % 2-10 for Fiestas and 25-100 for Kernel
VolCorr              ${{{TTAGS.vol_corr}}}    %  0) Disbale 1) Enable

%--------------------------------------------------------
% Kernel smoothing  related options
% 0) B-Spline 1)top hat 2)Bi_weight (1-x^2)^2 3)Epanechikov 4)CIC 5)TSC
TypeOfKernel           ${{{TTAGS.type_of_kernel}}}
KernelBiasCorrection   ${{{TTAGS.kernel_bias_correction}}}    % 0)none 1)shift central particle
AnisotropicKernel      ${{{TTAGS.anisotropy_kernel}}}    % 0) Isotropic 1) Anisotropic
Anisotropy             ${{{TTAGS.anisotropy}}}    % fix minimum c/a minor/major axis ratio
DesNumNgbA             ${{{TTAGS.des_num_ngb_a}}}   % Neighbors for cal covar metric for Anisotropic Ker
%--------------------------------------------------------
% other miscellaneous option
TypeListOn        ${{{TTAGS.type_list_on}}}
PeriodicBoundaryOn ${{{TTAGS.periodic_boundary_on}}}
%--------------------------------------------------------""")
DEFAULT_FOR_PARAMFILE = {
    TTAGS.fname: TO_ENBID_FILENAME,
    # TTAGS.des_num_ngb: DEFAULT_NGB,
    TTAGS.spatial_scale: 1.0,
    TTAGS.part_boundary: 7,
    TTAGS.node_splitting_criterion: 1,
    TTAGS.cubic_cells: 0,
    TTAGS.median_splitting_on: 1,
    TTAGS.type_of_smoothing: 3,
    TTAGS.vol_corr: 1,
    TTAGS.type_of_kernel: 3,
    TTAGS.kernel_bias_correction: 1,
    TTAGS.anisotropy_kernel: 0,
    TTAGS.anisotropy: 0,
    TTAGS.type_list_on: 0,
    TTAGS.periodic_boundary_on: 0
}


TEMP_DIR = tempfile.TemporaryDirectory()

ENBID_CPP = pathlib.Path(__file__).resolve().parent / ENBID2

@dataclass()#frozen=True)
class Constants(metaclass=Singleton):
    enbid: pathlib.Path  = ENBID_CPP / ENBID_EXEC
    enbid_paramfile: str = ENBID_PARAMFILE

    @property
    def usedvalues(self):
        return f"{self.enbid_paramfile}{USEDVALUES_SUFFIX}"

CONSTANTS = Constants()
