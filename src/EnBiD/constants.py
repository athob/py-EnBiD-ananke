#!/usr/bin/env python
"""
Package parameters
"""
import pathlib
import tempfile
from string import Template

__all__ = ['NAME', 'LOG_DIR', 'SRC_DIR', 'ENBID2', 'ENBID_URL', 'ENBID', 'TO_ENBID_FILENAME', 'ENBID_PARAMFILE', 'USEDVALUES', 'SNAPSHOT_FILEBASE', 'ENBID_OUT_EXT', 'ENBID_PARAMFILE_TEMPLATE']

NAME = 'EnBiD'
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

ENBID_PARAMFILE_TEMPLATE = Template("""%  Input and Output
InitCondFile     ${fname}

%-------------------------------------------------------
ICFormat                  0     % O)ASCII 1)Gadget 2)User defined
SnapshotFileBase        _d3n${ngb}

%-------------------------------------------------------
% Tree related options
SpatialScale            1.0 %  x->x/SpatialScale and v->v
PartBoundary            7   % Min particles in a node to do boundary correction
NodeSplittingCriterion  1   % 0)Alternate 1) Min Entropy
CubicCells              0   % use 1 in spherically symmetric systems
MedianSplittingOn       1   %

%--------------------------------------------------------
% Smoothing options  AM=adaptive metric Ker=Kernel Sp=Spherical Pr=Product
% 0) None 1)FiEstAS 2)Ker Sp Normal 3)Ker Sp AM 4)KerPr Normal 5)KerPr AM
TypeOfSmoothing      3
DesNumNgb            ${ngb}   % 2-10 for Fiestas and 25-100 for Kernel
VolCorr              1    %  0) Disbale 1) Enable

%--------------------------------------------------------
% Kernel smoothing  related options
% 0) B-Spline 1)top hat 2)Bi_weight (1-x^2)^2 3)Epanechikov 4)CIC 5)TSC
TypeOfKernel           3
KernelBiasCorrection   1    % 0)none 1)shift central particle
AnisotropicKernel      1    % 0) Isotropic 1) Anisotropic
Anisotropy             0    % fix minimum c/a minor/major axis ratio
DesNumNgbA             64   % Neighbors for cal covar metric for Anisotropic Ker
%--------------------------------------------------------
% other miscellaneous option
TypeListOn        0
PeriodicBoundaryOn 0
%--------------------------------------------------------""")


TEMP_DIR = tempfile.TemporaryDirectory()

ENBID_CPP = pathlib.Path(__file__).resolve().parent / ENBID2
ENBID = ENBID_CPP / ENBID_EXEC

USEDVALUES = '{}{}'.format(ENBID_PARAMFILE, USEDVALUES_SUFFIX)

