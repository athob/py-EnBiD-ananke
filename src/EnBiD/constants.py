#!/usr/bin/env python
"""
Package parameters
"""
import os
from string import Template

__all__ = ['ENBID', 'ENBID_PARAMFILE_TEMPLATE']

ENBID2 = 'Enbid-2.0'
ENBID_CPP = os.path.join(os.path.split(os.path.abspath(__file__))[0], ENBID2)
ENBID_EXEC = 'Enbid'

ENBID = os.path.join(ENBID_CPP, ENBID_EXEC)

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