#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2026  Adrien CR Thob
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
Tests of the tools that build EnBiD when the package is installed. Nothing is downloaded or compiled for
real: the commands on the PATH are fakes (their versions are known), the download is replaced by one that
makes a tarball on the spot, and EnBiD is a toy with a Makefile that has the lines the tools look for.
The module imports setuptools and distutils, which are not always there: without them, nothing is run here.
"""
import contextlib
import io
import os
import pathlib
import re
import shutil
import tarfile
import urllib.error
import urllib.request
from unittest import mock

import pytest

pytest.importorskip('setuptools')
pytest.importorskip('distutils.errors')

from distutils.errors import CompileError

from .. import _build_utils as build
from ..enbid_ananke import CONSTANTS
from .utils import in_tmp_wd, fake_commands

GOOD_COMMANDS = {'tar': 'tar (GNU tar) 1.34', 'make': 'GNU Make 4.3', 'g++': 'g++ (GCC) 11.2.0'}

needs_tar = pytest.mark.skipif(shutil.which('tar') is None, reason='needs tar')
needs_make = pytest.mark.skipif(shutil.which('make') is None, reason='needs make')


@contextlib.contextmanager
def quiet():
    """The tools print to the terminal, even when the output is redirected: not in the tests."""
    with mock.patch.object(build, 'say', lambda text: None):
        yield


# --- the system has what is needed

def test_a_system_with_everything_is_accepted():
    with fake_commands(GOOD_COMMANDS):
        build.verify_system_dependencies()


@pytest.mark.parametrize('missing, words', [('tar', 'tar'), ('make', 'gnumake'), ('g++', 'C++ compiler')])
def test_a_command_that_is_missing_is_refused_by_name(missing, words):
    with fake_commands({name: output for name, output in GOOD_COMMANDS.items() if name != missing}):
        with pytest.raises(OSError, match=re.escape(words)):
            build.verify_system_dependencies()


@pytest.mark.parametrize('make, accepted', [('3.82', True), ('3.81', False), ('3.82.1', True), ('4.4.1', True), ('3.9', False)])
def test_the_oldest_make_is_3_82(make, accepted):
    with fake_commands(dict(GOOD_COMMANDS, make=f'GNU Make {make}')):
        if accepted:
            build.verify_system_dependencies()
        else:
            with pytest.raises(OSError, match='3.82'):
                build.verify_system_dependencies()


@pytest.mark.parametrize('gpp, accepted', [('8.5.0', True), ('8.4.9', False), ('13.2.0', True), ('7.5.0', False)])
def test_the_oldest_gpp_is_8_5(gpp, accepted):
    with fake_commands(dict(GOOD_COMMANDS, **{'g++': f'g++ (GCC) {gpp}'})):
        if accepted:
            build.verify_system_dependencies()
        else:
            with pytest.raises(OSError, match='8.5'):
                build.verify_system_dependencies()


# --- the files of the package

@in_tmp_wd
def test_all_files_lists_the_files_of_the_folders_relative_to_the_base():
    for name in ('base/pkg/Enbid-2.0/src/Makefile', 'base/pkg/Enbid-2.0/Enbid.3d', 'base/pkg/__license__/LICENSE',
                 'base/pkg/__init__.py'):
        pathlib.Path(name).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(name).write_text('x')
    files = build.all_files('Enbid-2.0', '__license__', basedir='base/pkg')
    assert sorted(files) == ['Enbid-2.0/Enbid.3d', 'Enbid-2.0/src/Makefile', '__license__/LICENSE']   # not __init__.py


@in_tmp_wd
def test_all_files_of_a_folder_that_is_not_there_is_empty():
    pathlib.Path('base').mkdir()
    assert build.all_files('nothing', basedir='base') == []


# --- downloading EnBiD

def fake_download(members, top='Enbid-2.0'):
    def urlretrieve(url, filename=None):
        with tarfile.open(filename, 'w:gz') as archive:
            for name, text in members.items():
                data = text.encode()
                info = tarfile.TarInfo(f"{top}/{name}")
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
        return filename, None
    return urlretrieve


@needs_tar
@in_tmp_wd
def test_enbid_is_downloaded_and_unpacked():
    pathlib.Path('work').mkdir()
    enbid_dir = pathlib.Path('work/Enbid-2.0').absolute()
    with quiet(), mock.patch.object(urllib.request, 'urlretrieve', fake_download({'src/Makefile': 'all:\n', 'README': 'r'})):
        build.download_enbid(enbid_dir)
    assert (enbid_dir / 'src' / 'Makefile').is_file() and (enbid_dir / 'README').is_file()
    assert [p.name for p in pathlib.Path('work').iterdir()] == ['Enbid-2.0']      # the tarball does not stay


@needs_tar
@in_tmp_wd
def test_what_was_there_before_is_replaced():
    pathlib.Path('work/Enbid-2.0').mkdir(parents=True)
    (pathlib.Path('work/Enbid-2.0') / 'stale').write_text('old')
    with quiet(), mock.patch.object(urllib.request, 'urlretrieve', fake_download({'README': 'new'})):
        build.download_enbid(pathlib.Path('work/Enbid-2.0').absolute())
    assert not (pathlib.Path('work/Enbid-2.0') / 'stale').exists()
    assert (pathlib.Path('work/Enbid-2.0') / 'README').read_text() == 'new'


@in_tmp_wd
def test_a_download_that_leaves_no_file_is_a_compile_error():
    pathlib.Path('work').mkdir()
    with quiet(), mock.patch.object(urllib.request, 'urlretrieve', lambda url, filename=None: None):
        with pytest.raises(CompileError, match='Cannot find downloaded file'):
            build.download_enbid(pathlib.Path('work/Enbid-2.0').absolute())


@needs_tar
@in_tmp_wd
def test_a_tarball_without_the_expected_folder_is_a_compile_error():
    pathlib.Path('work').mkdir()
    with quiet(), mock.patch.object(urllib.request, 'urlretrieve', fake_download({'README': 'r'}, top='Another-1.0')):
        with pytest.raises(CompileError, match='Error unpacking'):
            build.download_enbid(pathlib.Path('work/Enbid-2.0').absolute())


@in_tmp_wd
def test_a_download_that_fails_raises_its_own_error():
    pathlib.Path('work').mkdir()
    def refused(url, filename=None):
        raise urllib.error.URLError('no network')
    with quiet(), mock.patch.object(urllib.request, 'urlretrieve', refused):
        with pytest.raises(urllib.error.URLError):                      # not turned into a CompileError today
            build.download_enbid(pathlib.Path('work/Enbid-2.0').absolute())


# --- configuring and building EnBiD

# What the Makefile of EnBiD has, as far as the tools look at it: the executable, a line of warning flags, and
# a line of options for each dimension. This is a toy: building it writes a script, not a program.
MAKEFILE = """EXEC   = Enbid

OPT1   = -Wall
#OPT2   += -DDIM3
OPT2   += -DDIM6

CC     = g++

all: $(EXEC)

$(EXEC):
\t@echo building $(EXEC)
\t@printf '#!/bin/sh\\necho toy $(EXEC)\\n' > ../$(EXEC)
\t@chmod +x ../$(EXEC)

clean:
\t@echo cleaning
"""


def toy_enbid():
    makefile = pathlib.Path('Enbid-2.0/src/Makefile')
    makefile.parent.mkdir(parents=True)
    makefile.write_text(MAKEFILE)
    return pathlib.Path('Enbid-2.0').absolute()


@in_tmp_wd
def test_configuring_for_3d():
    enbid_dir = toy_enbid()
    build.configure_enbid(enbid_dir, enbid_exec=pathlib.Path('Enbid.3d'))
    lines = (enbid_dir / 'src' / 'Makefile').read_text().splitlines()
    assert lines[0] == 'EXEC   = Enbid.3d'                              # the name of the executable
    assert '#OPT1   = -Wall' in lines                                   # the warning flags are off
    assert 'OPT2   += -DDIM3' in lines and '#OPT2   += -DDIM6' in lines   # only the dimension asked for is on
    assert 'CC     = g++' in lines and 'all: $(EXEC)' in lines          # the rest is left alone


@in_tmp_wd
def test_configuring_for_6d():
    enbid_dir = toy_enbid()
    build.configure_enbid(enbid_dir, enbid_exec=pathlib.Path('Enbid.6d'))
    lines = (enbid_dir / 'src' / 'Makefile').read_text().splitlines()
    assert lines[0] == 'EXEC   = Enbid.6d'
    assert '#OPT2   += -DDIM3' in lines and 'OPT2   += -DDIM6' in lines


@in_tmp_wd
def test_configuring_for_one_dimension_then_the_other_ends_up_as_the_other():
    # download_and_compile_enbid configures the same Makefile for 3D, builds, then for 6D
    enbid_dir = toy_enbid()
    build.configure_enbid(enbid_dir, enbid_exec=pathlib.Path('Enbid.3d'))
    build.configure_enbid(enbid_dir, enbid_exec=pathlib.Path('Enbid.6d'))
    lines = (enbid_dir / 'src' / 'Makefile').read_text().splitlines()
    assert lines[0] == 'EXEC   = Enbid.6d'
    assert '#OPT2   += -DDIM3' in lines and 'OPT2   += -DDIM6' in lines


@in_tmp_wd
def test_configuring_twice_for_the_same_dimension_changes_nothing_more():
    enbid_dir = toy_enbid()
    build.configure_enbid(enbid_dir, enbid_exec=pathlib.Path('Enbid.3d'))
    once = (enbid_dir / 'src' / 'Makefile').read_text()
    build.configure_enbid(enbid_dir, enbid_exec=pathlib.Path('Enbid.3d'))
    assert (enbid_dir / 'src' / 'Makefile').read_text() == once


@needs_make
@in_tmp_wd
def test_compiling_makes_the_executable_and_keeps_the_log():
    enbid_dir = toy_enbid()
    with quiet(), mock.patch.object(build, 'ROOT_DIR', pathlib.Path('root').absolute()):
        build.compile_enbid(enbid_dir, enbid_exec=pathlib.Path('Enbid.3d'))
        assert (enbid_dir / 'Enbid.3d').is_file() and os.access(enbid_dir / 'Enbid.3d', os.X_OK)
        log = (build.ROOT_DIR / build.LOG_DIR / 'Enbid3d-make.log').read_text()
    assert 'building Enbid.3d' in log


@needs_make
@in_tmp_wd
def test_compiling_both_dimensions_makes_both_executables():
    enbid_dir = toy_enbid()
    with quiet(), mock.patch.object(build, 'ROOT_DIR', pathlib.Path('root').absolute()):
        build.compile_enbid(enbid_dir, enbid_exec=pathlib.Path('Enbid.3d'))
        build.compile_enbid(enbid_dir, enbid_exec=pathlib.Path('Enbid.6d'))
    assert (enbid_dir / 'Enbid.3d').is_file() and (enbid_dir / 'Enbid.6d').is_file()


@needs_make
@in_tmp_wd
def test_a_build_that_does_not_make_the_executable_is_a_compile_error():
    enbid_dir = toy_enbid()
    makefile = enbid_dir / 'src' / 'Makefile'
    makefile.write_text(makefile.read_text().replace("\t@printf", "\t@true #").replace("\t@chmod", "\t@true #"))
    with quiet(), mock.patch.object(build, 'ROOT_DIR', pathlib.Path('root').absolute()):
        with pytest.raises(CompileError):
            build.compile_enbid(enbid_dir, enbid_exec=pathlib.Path('Enbid.3d'))


@in_tmp_wd
def test_downloading_and_compiling_goes_through_both_dimensions_in_order():
    calls = []
    with mock.patch.object(build, 'ROOT_DIR', pathlib.Path('root').absolute()), \
            mock.patch.object(build, 'download_enbid', lambda enbid_dir: calls.append(('download', enbid_dir))), \
            mock.patch.object(build, 'compile_enbid', lambda enbid_dir, enbid_exec: calls.append(('compile', enbid_exec))):
        build.download_and_compile_enbid()
    expected_dir = pathlib.Path('root').absolute() / build.SRC_DIR / build.NAME / CONSTANTS.enbid2
    assert calls == [('download', expected_dir), ('compile', CONSTANTS.enbid3d), ('compile', CONSTANTS.enbid6d)]


# --- what the package is made of

@in_tmp_wd
def test_the_package_data_is_what_was_built_and_the_licenses():
    package = pathlib.Path(build.SRC_DIR, build.NAME)
    for name in (f'{CONSTANTS.enbid2}/Enbid.3d', f'{CONSTANTS.enbid2}/Enbid.6d', f'{CONSTANTS.enbid2}/src/main.cpp',
                 '__license__/LICENSE', '__init__.py'):
        (package / name).parent.mkdir(parents=True, exist_ok=True)
        (package / name).write_text('x')
    calls = []
    with mock.patch.object(build, 'verify_system_dependencies', lambda: calls.append('verify')), \
            mock.patch.object(build, 'download_and_compile_enbid', lambda: calls.append('build')):
        data = build.make_package_data()
    assert calls == ['verify', 'build']                                 # the system is checked before anything is downloaded
    assert list(data) == [build.NAME]
    assert sorted(data[build.NAME]) == [f'{CONSTANTS.enbid2}/Enbid.3d', f'{CONSTANTS.enbid2}/Enbid.6d',
                                        f'{CONSTANTS.enbid2}/src/main.cpp', '__license__/LICENSE']


def test_the_commands_of_the_build_are_those_of_versioneer_and_a_test_command():
    from setuptools.command.build_ext import build_ext
    commands = build.make_cmdclass()
    assert 'test' in commands
    assert 'sdist' in commands and 'build_py' in commands               # what versioneer adds
    assert issubclass(commands['build_ext'], build_ext)                 # versioneer supplies it, whether or not one is given


if __name__ == '__main__':
    pass
