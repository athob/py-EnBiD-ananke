#!/usr/bin/env python
"""
Contains the EnBiD module building utility tools. Credit to
https://github.com/GalacticDynamics-Oxford/Agama/blob/master/setup.py.
"""
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

ROOT_DIR = pathlib.Path(__file__).parent.parent
MIN_GPP_VERSION = Version("8.5")  # TODO can probably test with a lesser version
MIN_MAKE_VERSION = Version("3.82")


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
            for dirpath, dirnames, files in os.walk(basedir / path)
            for f in files]


def verify_system_dependencies():
    try:
        tar_version = Version(get_version_of_command("tar"))
    except FileNotFoundError:
        raise OSError("Your system does not have tar installed. Please install tar before proceeding")
    try:
        make_version = Version(get_version_of_command("make"))
    except FileNotFoundError:
        raise OSError("Your system does not have the utility gnumake installed. Please install one before proceeding")
    if make_version < MIN_MAKE_VERSION:
        raise OSError(f"Your system has gnumake v{make_version} installed, but Galaxia_ananke requires v{MIN_MAKE_VERSION}")
    try:
        gpp_version = Version(get_version_of_command("g++"))
    except FileNotFoundError:
        raise OSError("Your system does not have a C++ compiler installed. Please install one before proceeding")
    if gpp_version < MIN_GPP_VERSION:
        raise OSError(f"Your system has g++ v{gpp_version} installed, but Galaxia_ananke requires v{MIN_GPP_VERSION}")


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


def download_and_compile_enbid():
    enbid_dir = ROOT_DIR / SRC_DIR / NAME / CONSTANTS.enbid2
    download_enbid(enbid_dir)
    compile_enbid(enbid_dir)


def make_package_data():
    for_all_files = (CONSTANTS.enbid2, '__license__')
    ########## This can't be in MyBuildExt ##########
    verify_system_dependencies()
    download_and_compile_enbid()
    ############## Because of that bit ##############
    return {NAME: all_files(*for_all_files,
                                    basedir=pathlib.Path(SRC_DIR, NAME))}


def make_cmdclass():
    """
    """
    # Custom build step that manually creates the makefile and then calls 'make' to create the shared library
    class _build_ext(build_ext):
        def run(self):
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
        description = 'run tests'
        user_options = []

        def initialize_options(self): pass

        def finalize_options(self): pass

        def run(self): pass
    
    return versioneer.get_cmdclass({'build_ext': _build_ext, 'test': _test})
