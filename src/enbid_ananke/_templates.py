#!/usr/bin/env python
"""
Contains the EnBiD module templates.
"""
from string import Template
from dataclasses import dataclass

from ._builtin_utils import Singleton

__all__ = ['TTAGS', 'ENBID_PARAMFILE_TEMPLATE']

@dataclass(frozen=True)
class TemplateTags(metaclass=Singleton):
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

TTAGS = TemplateTags()

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


if __name__ == '__main__':
    raise NotImplementedError()
