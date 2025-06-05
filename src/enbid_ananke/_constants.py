#!/usr/bin/env python
"""
Contains the EnBiD module constants.
"""
import pathlib
from dataclasses import dataclass

from ._name import *
from ._builtin_utils import Singleton

__all__ = ['NAME', 'LOG_DIR', 'SRC_DIR', 'ENBID_URL', 'CONSTANTS', 'SNAPSHOT_FILEBASE', 'ENBID_OUT_EXT', 'HASH_EXT', 'HASH_ENCODING']

ENBID2 = 'Enbid-2.0'
ENBID_URL = 'https://sourceforge.net/projects/enbid/files/latest/download'
ENBID_EXEC = 'Enbid'
LOG_DIR = 'log'
SRC_DIR = 'src'

ENBID_PARAMFILE = 'enbid_paramfile'
USEDVALUES_SUFFIX = '_enbid-usedvalues'
SNAPSHOT_FILEBASE = 'SnapshotFileBase'
ENBID_OUT_EXT = 'est'
HASH_EXT = 'hash'
HASH_ENCODING = 'ascii'

@dataclass()
class Constants(metaclass=Singleton):
    enbid2: str          = ENBID2
    enbid_exec: str      = ENBID_EXEC
    _enbid: pathlib.Path = None
    enbid_paramfile: str = ENBID_PARAMFILE

    @property
    def enbid_cpp(self):
        return pathlib.Path(__file__).resolve().parent / self.enbid2
    
    @property
    def enbid(self):
        if isinstance(self._enbid, pathlib.Path):
            return self._enbid
        else:
            return self.enbid_cpp / self.enbid_exec
    
    @enbid.setter
    def enbid(self, path: pathlib.Path):
        self._enbid = path

    @property
    def usedvalues(self):
        return f"{self.enbid_paramfile}{USEDVALUES_SUFFIX}"

CONSTANTS = Constants()


if __name__ == '__main__':
    raise NotImplementedError()
