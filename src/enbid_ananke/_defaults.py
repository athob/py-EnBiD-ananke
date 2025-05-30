#!/usr/bin/env python
"""
Contains the EnBiD module defaults.
"""
import tempfile

from ._templates import *

__all__ = ['DEFAULT_NGB', 'DEFAULT_FOR_PARAMFILE']

TO_ENBID_FILENAME = 'to_enbid'
DEFAULT_NGB = 64

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


if __name__ == '__main__':
    raise NotImplementedError()
