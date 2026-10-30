#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2022  Adrien CR Thob
#
# This file is part of the py-EnBiD-ananke project,
# <https://github.com/athob/py-EnBiD-ananke>,  which is licensed
# under the GNU General Public License v2.0 or later (GPL-2.0-or-later).
# 
# The full copyright notice, including terms governing use, modification,
# and redistribution, is contained in the files LICENSE and COPYRIGHT,
# which can be found at the root of the source code distribution tree:
# - LICENSE <https://github.com/athob/py-EnBiD-ananke/blob/main/LICENSE>
# - COPYRIGHT <https://github.com/athob/py-EnBiD-ananke/blob/main/COPYRIGHT>
#
import os
import sys
import io
import tempfile
import pathlib
import stat
import struct
import contextlib
import functools

import numpy as np

from ..enbid_ananke import CONSTANTS, DEFAULT_FOR_PARAMFILE, TTAGS, ENBID_OUT_EXT

n_sample = 100

enbid_test_exec_script = """#!/usr/bin/env bash
echo $1
"""

def make_enbid_test_exec():
    CONSTANTS.enbid3d.write_text(enbid_test_exec_script)
    CONSTANTS.enbid3d.chmod(CONSTANTS.enbid3d.stat().st_mode | stat.S_IEXEC)
    return CONSTANTS.enbid3d

# A stand-in for the EnBiD executable that does what the real one does as far as the wrapper can
# tell: it reads the parameter file it is given, writes the file of the values it used, and writes
# a file of densities in the format the parameter file asks for (ASCII, or GADGET). The densities
# are made up, but depend on the input in a way a test can check: 1, 2, 3... for ASCII input,
# and ten times the mass of each particle for GADGET input. It also logs which executable ran.
fake_enbid_exec_script = """#!@PYTHON@
import pathlib, struct, sys

paramfile = pathlib.Path(sys.argv[1])
values = {}
for line in paramfile.read_text().splitlines():
    line = line.split('%')[0].strip()
    if line:
        key, value = line.split(None, 1)
        values[key] = value.strip()
pathlib.Path('@USEDVALUES@').write_text(''.join('%s   %s\\n' % item for item in values.items()))
with open('fake_enbid_calls', 'a') as log:
    log.write(pathlib.Path(sys.argv[0]).name + '\\n')
print(paramfile.name)

def records(data):
    blocks, position = [], 0
    while position < len(data):
        size = struct.unpack('<i', data[position:position + 4])[0]
        blocks.append(data[position + 4:position + 4 + size])
        position += 8 + size
    return blocks

source = values['InitCondFile']
output = pathlib.Path(source + values['SnapshotFileBase'] + '.@EXTENSION@')
if int(values['ICFormat']) == 1:
    header, _, _, _, mass = records(pathlib.Path(source).read_bytes())
    n = sum(struct.unpack('<6i', header[:24]))
    density = struct.pack('<%df' % n, *[10 * m for m in struct.unpack('<%df' % n, mass)])
    with output.open('wb') as f:
        for block in (bytes(256), density):
            f.write(struct.pack('<i', len(block)) + block + struct.pack('<i', len(block)))
else:
    n = len([line for line in pathlib.Path(source).read_text().splitlines() if line.strip()])
    output.write_text('\\n'.join(str(float(i + 1)) for i in range(n)))
"""


@contextlib.contextmanager
def preserved_enbid_paths():
    """
    The paths of the executables live in a global (CONSTANTS): whatever a test sets there
    is put back afterwards, so that it does not leak into the tests that run after it.
    """
    saved = CONSTANTS._enbid3d, CONSTANTS._enbid6d
    try:
        yield
    finally:
        CONSTANTS._enbid3d, CONSTANTS._enbid6d = saved


@contextlib.contextmanager
def fake_enbid():
    """
    Puts the stand-in for EnBiD, as a 3D and a 6D executable, in the current directory, and makes
    the wrapper use them until the end of the block. Needs a Unix system, like the package.
    """
    script = (fake_enbid_exec_script.replace('@PYTHON@', sys.executable)
              .replace('@USEDVALUES@', CONSTANTS.usedvalues).replace('@EXTENSION@', ENBID_OUT_EXT))
    with preserved_enbid_paths():
        for dimension in ('3d', '6d'):
            executable = pathlib.Path(f"Enbid.{dimension}").absolute()
            executable.write_text(script)
            executable.chmod(executable.stat().st_mode | stat.S_IEXEC)
            setattr(CONSTANTS, f"enbid{dimension}", executable)
        yield


def with_fake_enbid(func):
    """Runs the test in a temporary directory, with the stand-in for EnBiD (see fake_enbid)."""
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        with tmp_wd(), fake_enbid():
            func(*args, **kwargs)
    return wrapped_func


def read_paramfile(path):
    """The parameter file the wrapper wrote, as a dictionary of strings."""
    values = {}
    for line in pathlib.Path(path).read_text().splitlines():
        line = line.split('%')[0].strip()
        if line:
            key, value = line.split(None, 1)
            values[key] = value.strip()
    return values


def read_gadget_records(path):
    """
    The blocks of a GADGET-1 file, as bytes: the size written before each one has to be the size
    written after it, or this raises an AssertionError.
    """
    data = pathlib.Path(path).read_bytes()
    blocks, position = [], 0
    while position < len(data):
        size = struct.unpack('<i', data[position:position + 4])[0]
        block = data[position + 4:position + 4 + size]
        assert struct.unpack('<i', data[position + 4 + size:position + 8 + size])[0] == size
        blocks.append(block)
        position += 8 + size
    return blocks


def write_enbid_binary_output(path, density):
    """A file of densities in the GADGET format EnBiD writes: a header of 256 bytes, then the densities."""
    density = np.asarray(density, dtype=np.float32).tobytes()
    with open(path, 'wb') as f:
        for block in (bytes(256), density):
            f.write(struct.pack('<i', len(block)) + block + struct.pack('<i', len(block)))


def simulate_enbid_output(name, tag='_d3n64', values=[], binary=False):
    path = pathlib.Path(name)
    path.mkdir()
    output = path / f"{DEFAULT_FOR_PARAMFILE[TTAGS.fname]}{tag}.{ENBID_OUT_EXT}"
    if binary:
        (path / CONSTANTS.usedvalues).write_text(f"SnapshotFileBase                   {tag}\nICFormat   1")
        write_enbid_binary_output(output, values)
    else:
        (path / CONSTANTS.usedvalues).write_text(f"SnapshotFileBase                   {tag}")
        output.write_text("\n".join(map(str,values)))

@contextlib.contextmanager
def tmp_wd():
    """
    Changes working directory to a temporary one
    and returns to previous on exit.
    Credit to https://stackoverflow.com/a/42441759
    """
    prev_cwd = pathlib.Path.cwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            yield
        finally:
            os.chdir(prev_cwd)

def in_tmp_wd(func):
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        with tmp_wd():
            func(*args, **kwargs)
    return wrapped_func

class list_stdout(list):
    """
    Credit to https://stackoverflow.com/a/16571630
    """
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout


if __name__ == '__main__':
    pass
