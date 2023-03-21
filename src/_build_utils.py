#!/usr/bin/env python
"""
Contains the EnBiD module building utility tools.
"""
import pathlib
import shutil
import sys
import re
import fileinput
import subprocess
import urllib.request
from distutils.errors import CompileError

from .constants import *

__all__ = ['say', 'all_files', 'download_enbid', 'compile_enbid']

ROOT_DIR = pathlib.Path(__file__).parent.parent


# force printing to the terminal even if stdout was redirected
def say(text):
    text += ' '
    sys.stdout.write(text)
    sys.stdout.flush()
    if not sys.stdout.isatty():
        # output was redirected, but we still try to send the message to the terminal
        try:
            if pathlib.Path('/dev/tty').exists():
                with open('/dev/tty', 'w') as out:
                    out.write(text)
                    out.flush()
        except (OSError, PermissionError):
            # /dev/tty may not exist or may not be writable!
            pass


# get the list of all files in the given directories (including those in nested directories)
def all_files(*paths, basedir='.'):
    basedir = pathlib.Path(basedir)
    return [str(pathlib.Path(dirpath, f).relative_to(basedir))
            for path in paths
            for dirpath, dirnames, files in pathlib.os.walk(basedir / path)
            for f in files]


def download_enbid(enbid_dir):
    say("\nDownloading Enbid")
    if enbid_dir.is_dir():
        shutil.rmtree(enbid_dir)
    tarfile = enbid_dir.with_suffix('.tar.gz')
    try:
        urllib.request.urlretrieve(ENBID_URL, filename=tarfile)
        if tarfile.is_file():
            say("\nUnpacking Enbid")
            subprocess.call(['tar', 'xzvf', tarfile, '-C', tarfile.parent],
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            tarfile.unlink()
            if not enbid_dir.is_dir():
                raise RuntimeError("Error unpacking Enbid")
        else:
            raise RuntimeError("Cannot find downloaded file")
    except RuntimeError as e:
        raise CompileError(str(e) + "\nError downloading Enbid, aborting...\n")


def configure_enbid(enbid_dir):
    makefile = enbid_dir / 'src' / 'Makefile'
    for line in fileinput.input(makefile, inplace=True):
        if bool(re.match(r".*OPT2.*=", line)):  # TODO have both 3D and 6D version separately available
            line = re.sub(r'.*OPT2',  '{}OPT2'.format('' if re.match(r".*-DDIM3", line) else '#'), line)
        print(line, end='')


def make_enbid(enbid_dir):
    with (ROOT_DIR / LOG_DIR / 'Enbid-make.log').open('w') as f:
        result = subprocess.call(f"make", cwd=enbid_dir / 'src', stdout=f, stderr=f)
    if result != 0 or not (enbid_dir / 'Enbid').is_file():
        raise CompileError(f"Enbid compilation failed (check {pathlib.Path('.', LOG_DIR, 'Enbid-make.log')})")


def compile_enbid(enbid_dir):
    enbid_dir = pathlib.Path(enbid_dir).resolve()
    say("\nCompiling Enbid")
    (ROOT_DIR / LOG_DIR).mkdir(parents=True, exist_ok=True)
    say("\n\tConfiguring")
    configure_enbid(enbid_dir)
    say("\n\tRunning make")
    make_enbid(enbid_dir)
    say("\n")
