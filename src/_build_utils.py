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
"""
Contains the EnBiD module building utility tools. Credit to
https://github.com/GalacticDynamics-Oxford/Agama/blob/master/setup.py.
"""
import platform
import os
import pathlib
import shutil
import sys
import re
import fileinput
import subprocess
import urllib.request
from distutils.errors import CompileError
from setuptools.command.build_ext import build_ext
from setuptools import Command
from packaging.version import Version

from ._builtin_utils import get_version_of_command
from ._constants import *
from . import versioneer

__all__ = ['make_package_data', 'make_cmdclass']

if platform.system() == "Windows":
    raise OSError(f"Windows compatibility is not currently supported by {NAME}. We apologize for the inconvenience.")

ROOT_DIR = pathlib.Path(__file__).parent.parent
MIN_GPP_VERSION = Version("8.5")  # TODO can probably test with a lesser version
MIN_MAKE_VERSION = Version("3.82")


# force printing to the terminal even if stdout was redirected
def say(text):
    """
    Write a text, followed by a space, to the standard output and, if that is
    redirected, to the terminal too.

    Parameters
    ----------
    text : str
        What to write.
    """
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
    """
    List the files in the given folders, those in nested folders included.

    Parameters
    ----------
    *paths : str
        Folders, relative to ``basedir``.
    basedir : str or pathlib.Path, optional
        The folder the paths are relative to. Default to the current folder.

    Returns
    -------
    files : list of str
        The path of every file, relative to ``basedir``.
    """
    basedir = pathlib.Path(basedir)
    return [str(pathlib.Path(dirpath, f).relative_to(basedir))
            for path in paths
            for dirpath, dirnames, files in os.walk(basedir / path)
            for f in files]


def verify_system_dependencies():
    """
    Check that the system has what building EnBiD needs: tar, GNU make (at
    least MIN_MAKE_VERSION) and the C++ compiler g++ (at least MIN_GPP_VERSION).

    Raises
    ------
    OSError
        Saying which of them is missing, or too old.
    """
    try:
        Version(get_version_of_command("tar"))
    except FileNotFoundError:
        raise OSError("Your system does not have tar installed. Please install tar before proceeding")
    try:
        make_version = Version(get_version_of_command("make"))
    except FileNotFoundError:
        raise OSError("Your system does not have the utility gnumake installed. Please install one before proceeding")
    if make_version < MIN_MAKE_VERSION:
        raise OSError(f"Your system has gnumake v{make_version} installed, but {NAME} requires v{MIN_MAKE_VERSION}")
    try:
        gpp_version = Version(get_version_of_command("g++"))
    except FileNotFoundError:
        raise OSError("Your system does not have a C++ compiler installed. Please install one before proceeding")
    if gpp_version < MIN_GPP_VERSION:
        raise OSError(f"Your system has g++ v{gpp_version} installed, but {NAME} requires v{MIN_GPP_VERSION}")


def download_enbid(enbid_dir):
    """
    Download EnBiD and unpack it, replacing what was in its folder.

    The tarball is downloaded from ENBID_URL next to the folder, unpacked with
    tar, and deleted.

    Parameters
    ----------
    enbid_dir : pathlib.Path
        Where EnBiD is to be: the tarball has to unpack to a folder of that name.

    Raises
    ------
    CompileError
        If nothing was downloaded, or the tarball did not unpack to ``enbid_dir``.
    urllib.error.URLError
        If the download itself failed: it is not turned into a CompileError.
    """
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


def configure_enbid(enbid_dir, enbid_exec = CONSTANTS.enbid3d):
    """
    Edit the Makefile of EnBiD, in place, to build the executable of one dimension.

    The line of warning flags is commented out, the line of options of the
    dimension of ``enbid_exec`` is the only one of the options lines left
    uncommented (``-DDIM3`` for a 3D executable, ``-DDIM6`` for a 6D one), and
    the name of the executable becomes that of ``enbid_exec``. Doing it again
    for the other dimension, on the same Makefile, switches it over.

    Parameters
    ----------
    enbid_dir : pathlib.Path
        The folder of EnBiD, which has its Makefile in ``src``.
    enbid_exec : pathlib.Path, optional
        The executable to build: its suffix gives the dimension, and its name the
        name the built executable gets. Default to the 3D one.
    """
    makefile = enbid_dir / 'src' / 'Makefile'
    for line in fileinput.input(makefile, inplace=True):
        if bool(re.match(r".*OPT1.*=", line)):  # catch line with warning flag to comment it
            line = re.sub(r'.*OPT1', '#OPT1', line)
        if bool(re.match(r".*OPT2.*=", line)):  # catch lines with dimension flags and keep the right uncommented while commenting the others
            line = re.sub(r'.*OPT2', '{}OPT2'.format('' if re.match(rf".*-DDIM{re.findall(r'.(.*)d', enbid_exec.suffix)}", line) else '#'), line)
        if bool(re.match(r"EXEC\s*=", line)):  # catch line that defines the executable name to modify it accordingly
            line = re.sub(re.split(r"EXEC\s*=", line)[1].strip(), enbid_exec.name, line)
        print(line, end='')


def make_enbid(enbid_dir, enbid_exec = CONSTANTS.enbid3d):
    """
    Run make in the folder of EnBiD, then make clean, with their output in a log.

    The log is ``log/Enbid3d-make.log`` or ``log/Enbid6d-make.log``, in the root
    of the repository, which must have a ``log`` folder.

    Parameters
    ----------
    enbid_dir : pathlib.Path
        The folder of EnBiD, configured for ``enbid_exec`` (see configure_enbid).
    enbid_exec : pathlib.Path, optional
        The executable that is built. Default to the 3D one.

    Raises
    ------
    CompileError
        If the executable is not there afterwards, or if make clean, which runs
        last, exits with an error.
    """
    with (ROOT_DIR / LOG_DIR / f'Enbid{enbid_exec.suffix.replace(".","")}-make.log').open('w') as f:
        result = subprocess.call("make", cwd=enbid_dir / 'src', stdout=f, stderr=f)
        result = subprocess.call(["make", "clean"], cwd=enbid_dir / 'src', stdout=f, stderr=f)
    if result != 0 or not (enbid_dir / enbid_exec.name).is_file():
        raise CompileError(f"Enbid compilation failed (check {pathlib.Path('.', LOG_DIR, 'Enbid-make.log')})")


def compile_enbid(enbid_dir, enbid_exec = CONSTANTS.enbid3d):
    """
    Build the executable of one dimension: make the folder of the logs if there
    is none, configure the Makefile (see configure_enbid), and run make (see
    make_enbid).

    Parameters
    ----------
    enbid_dir : pathlib.Path or str
        The folder of EnBiD.
    enbid_exec : pathlib.Path, optional
        The executable to build. Default to the 3D one.

    Raises
    ------
    CompileError
        If the build failed.
    """
    enbid_dir = pathlib.Path(enbid_dir).resolve()
    say(f"\nCompiling Enbid{enbid_exec.suffix.replace('.','')}")
    (ROOT_DIR / LOG_DIR).mkdir(parents=True, exist_ok=True)
    say("\n\tConfiguring")
    configure_enbid(enbid_dir, enbid_exec=enbid_exec)
    say("\n\tRunning make")
    make_enbid(enbid_dir, enbid_exec=enbid_exec)
    say("\n")


def download_and_compile_enbid():
    """
    Download EnBiD into the package, and build its 3D and then its 6D executable.

    Raises
    ------
    CompileError
        If the download or a build failed.
    """
    enbid_dir = ROOT_DIR / SRC_DIR / NAME / CONSTANTS.enbid2
    download_enbid(enbid_dir)
    compile_enbid(enbid_dir, enbid_exec = CONSTANTS.enbid3d)
    compile_enbid(enbid_dir, enbid_exec = CONSTANTS.enbid6d)


def make_package_data():
    """
    Build EnBiD, and list the files the package ships.

    The system is checked, EnBiD is downloaded and built (3D and 6D), and the
    files that leaves in the package are listed: the folder of EnBiD, with its
    executables, and the licenses. This is done when setup.py runs, and not by
    a build command (see the comments in the code).

    Returns
    -------
    package_data : dict
        The name of the package, with the files to ship with it, relative to it.

    Raises
    ------
    OSError
        If the system lacks what building EnBiD needs.
    CompileError
        If the download or a build failed.
    """
    for_all_files = (CONSTANTS.enbid2, '__license__')
    ########## This can't be in MyBuildExt ##########
    verify_system_dependencies()
    download_and_compile_enbid()
    ############## Because of that bit ##############
    return {NAME: all_files(*for_all_files,
                                    basedir=pathlib.Path(SRC_DIR, NAME))}


def make_cmdclass():
    """
    Give the commands of setup.py: those of versioneer, with a build_ext and a
    test command that do nothing more than the standard ones, or nothing.

    Returns
    -------
    cmdclass : dict
        The commands, by name.
    """
    # Custom build step that manually creates the makefile and then calls 'make' to create the shared library
    class _build_ext(build_ext):
        """The build_ext command, to which what building EnBiD may need is to be added: it is done by make_package_data."""
        def run(self):
            """Run build_ext."""
            build_ext.run(self)
            # try:
            #     say("\nTesting if Enbid is available...")
            #     enbid_exists = bool(subprocess.call('Enbid'))
            #     say("Done\n")
            # except (PermissionError, OSError):
            #     say("Absent\n")
            #     enbid_exists = False
            enbid_exists = False  # TODO
            if not enbid_exists:
                ########## This can't be in MyBuildExt ##########
                # enbid_dir = ROOT_DIR / SRC_DIR / NAME / CONSTANTS.enbid2
                # download_enbid(enbid_dir)
                # compile_enbid(enbid_dir)
                #################################################
                pass

    # TODO
    class _test(Command):
        """A test command, which is not implemented yet and does nothing."""
        description = 'run tests'
        user_options = []

        def initialize_options(self):
            """There is nothing to initialize."""

        def finalize_options(self):
            """There is nothing to finalize."""

        def run(self):
            """Do nothing."""
    
    return versioneer.get_cmdclass({'build_ext': _build_ext, 'test': _test})
