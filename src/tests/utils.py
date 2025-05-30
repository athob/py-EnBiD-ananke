#!/usr/bin/env python
import os
import sys
import io
import tempfile
import pathlib
import stat
import contextlib
import functools

from ..enbid_ananke import CONSTANTS, DEFAULT_FOR_PARAMFILE, TTAGS, ENBID_OUT_EXT

n_sample = 100

enbid_test_exec_script = """#!/usr/bin/env bash
echo $1
"""

def make_enbid_test_exec():
    CONSTANTS.enbid.write_text(enbid_test_exec_script)
    CONSTANTS.enbid.chmod(CONSTANTS.enbid.stat().st_mode | stat.S_IEXEC)
    return CONSTANTS.enbid

def simulate_enbid_output(name, tag='_d3n64', values=[]):
    path = pathlib.Path(name)
    path.mkdir()
    (path / CONSTANTS.usedvalues).write_text(f"SnapshotFileBase                   {tag}")
    (path / f"{DEFAULT_FOR_PARAMFILE[TTAGS.fname]}{tag}.{ENBID_OUT_EXT}").write_text("\n".join(map(str,values)))

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
