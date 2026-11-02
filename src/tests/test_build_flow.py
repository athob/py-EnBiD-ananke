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
Tests of how the package is built, the way the tools that build it do it: pip and build call the hooks of
PEP 517, and each hook runs setup.py in a Python of its own. What these tests count is how many times EnBiD
is downloaded and built by each of them, and what the sdist and the wheel hold at the end.

EnBiD is a toy here, so that nothing is downloaded and the build takes no time: the download is replaced by
a tarball made on the spot, and its Makefile writes a script as the executable and adds a line to a file each
time it is run. The build runs in a copy of the repository that is made a git repository of its own, because
versioneer asks git for the version, and the .git of this checkout cannot be copied: in a submodule or a
worktree it is a file that points elsewhere. It needs the git command, and the tools EnBiD needs: without
them, nothing is run here.
"""
import functools
import gzip
import hashlib
import io
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from typing import Any, Dict

import pytest

pytest.importorskip('setuptools')
pytest.importorskip('distutils.errors')

from .. import _build_utils as build

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXECUTABLES = ('Enbid.3d', 'Enbid.6d')

# What the Makefile of EnBiD has, as far as the tools look at it (see test_build_utils.py), and a line added to
# the file of the environment variable COUNTER each time EnBiD is built.
TOY_MAKEFILE = (
    "EXEC   = Enbid\n\nOPT1   = -Wall\n#OPT2   += -DDIM3\nOPT2   += -DDIM6\n\nall: $(EXEC)\n\n$(EXEC):\n"
    "\t@echo built >> $(COUNTER)\n\t@printf '#!/bin/sh\\necho toy $(EXEC)\\n' > ../$(EXEC)\n\t@chmod +x ../$(EXEC)\n\n"
    "clean:\n\t@true\n")

# Python runs this file when it starts, in every Python the hooks start: the download copies the toy tarball.
SITECUSTOMIZE = '''
import os, shutil, urllib.request
if os.environ.get("ENBID_TOY_TARBALL"):
    def urlretrieve(url, filename=None, *args, **kwargs):
        shutil.copyfile(os.environ["ENBID_TOY_TARBALL"], filename)
        return filename, None
    urllib.request.urlretrieve = urlretrieve
'''


def toy_tarball() -> bytes:
    """A tarball of a toy EnBiD, made the same way every time."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        for name, text in (('src/Makefile', TOY_MAKEFILE), ('src/main.cpp', 'int main() {}\n'), ('README', 'toy EnBiD\n')):
            data = text.encode()
            info = tarfile.TarInfo(f"Enbid-2.0/{name}")
            info.size, info.mtime = len(data), 0
            archive.addfile(info, io.BytesIO(data))
    return gzip.compress(buffer.getvalue(), mtime=0)


def without_git_variables(environment: Dict[str, str]) -> Dict[str, str]:
    """The environment, without what git sets for its hooks (GIT_DIR...): it would point git at the repository of the hook."""
    return {name: value for name, value in environment.items() if not name.startswith('GIT_')}


def git(directory: pathlib.Path, *arguments: str) -> None:
    subprocess.run(['git', '-c', 'commit.gpgsign=false', '-c', 'user.name=build flow test',
                    '-c', 'user.email=build-flow-test@example.invalid', *arguments],
                   cwd=str(directory), env=without_git_variables(dict(os.environ)), check=True, capture_output=True)


def copy_of_the_repository(destination: pathlib.Path, checksum: str, with_git: bool = True) -> pathlib.Path:
    """
    The files that building needs, and not what an earlier build left, made a git repository of their own with
    one commit (unless with_git is False: the files alone). The copy expects the checksum given, that of the toy
    tarball, and not that of the real EnBiD.
    """
    ignored = shutil.ignore_patterns('.git', '__pycache__', '*.egg-info', 'build', 'dist', 'log', 'Enbid-2.0', 'docs', '.github',
                                     'tests', '.mypy_cache', '.pytest_cache')
    shutil.copytree(ROOT, destination, ignore=ignored, symlinks=True)
    constants = destination / 'src' / 'enbid_ananke' / '_constants.py'
    text = constants.read_text()
    replaced = re.sub(r"^ENBID_SHA256 = '[0-9a-f]{64}'$", f"ENBID_SHA256 = '{checksum}'", text, flags=re.MULTILINE)
    assert replaced != text, "the checksum of EnBiD was not found in _constants.py"
    constants.write_text(replaced)
    if with_git:
        git(destination, 'init', '-q')
        git(destination, 'add', '-A')
        git(destination, 'commit', '-q', '-m', 'the copy')
    return destination


def check_building_is_possible() -> None:
    if shutil.which('git') is None:
        pytest.skip('versioneer needs git')
    try:
        build.verify_system_dependencies()
    except OSError as error:
        pytest.skip(str(error))
    try:
        import setuptools.command.bdist_wheel   # setuptools 70.1 and later
    except ImportError:
        pytest.importorskip('wheel')


def run_hook(tree: pathlib.Path, environment: Dict[str, str], hook: str, output: pathlib.Path) -> None:
    calls = {'get_requires_for_build_wheel': "b.get_requires_for_build_wheel()",
             'prepare_metadata_for_build_wheel': f"b.prepare_metadata_for_build_wheel({str(output)!r})",
             'build_wheel': f"b.build_wheel({str(output)!r})",
             'get_requires_for_build_sdist': "b.get_requires_for_build_sdist()",
             'build_sdist': f"b.build_sdist({str(output)!r})"}
    result = subprocess.run([sys.executable, '-c', f"import setuptools.build_meta as b; {calls[hook]}"],
                            cwd=str(tree), env=environment, capture_output=True, text=True)
    assert result.returncode == 0, f"{hook} failed:\n{result.stderr[-2000:]}"


@functools.lru_cache(maxsize=None)
def flows() -> Dict[str, Any]:
    """Build the package every way the tools do, once for all the tests, and say what happened."""
    check_building_is_possible()
    work = pathlib.Path(tempfile.mkdtemp(prefix='enbid_ananke_build_flow_'))
    try:
        site = work / 'site'
        site.mkdir()
        (site / 'sitecustomize.py').write_text(SITECUSTOMIZE)
        toy = toy_tarball()
        (work / 'toy.tar.gz').write_bytes(toy)
        checksum = hashlib.sha256(toy).hexdigest()
        counter = work / 'counter'
        environment = dict(without_git_variables(dict(os.environ)), PYTHONPATH=str(site), ENBID_TOY_TARBALL=str(work / 'toy.tar.gz'),
                           COUNTER=str(counter))

        def builds() -> int:
            return len(counter.read_text().split()) // 2 if counter.exists() else 0    # one line per dimension

        result: Dict[str, Any] = {'builds': {}}

        def hook(tree: pathlib.Path, name: str, output: pathlib.Path, label: str = '') -> None:
            before = builds()
            run_hook(tree, environment, name, output)
            result['builds'][label + name] = builds() - before

        # what pip does, with build isolation: it asks what is needed, what the package is, and then builds the wheel
        tree = copy_of_the_repository(work / 'pip', checksum)
        wheels = work / 'wheels'
        wheels.mkdir()
        for name in ('get_requires_for_build_wheel', 'prepare_metadata_for_build_wheel', 'build_wheel'):
            hook(tree, name, wheels)
        wheel = next(wheels.glob('*.whl'))
        with zipfile.ZipFile(wheel) as archive:
            result['wheel'] = {info.filename: (info.external_attr >> 16) & 0o111 for info in archive.infolist()}

        # an sdist made in that same tree, where EnBiD has just been built: what a developer, or CI after an install, has
        dirty = work / 'dirty'
        dirty.mkdir()
        hook(tree, 'build_sdist', dirty, label='(in a tree that built EnBiD) ')
        with tarfile.open(next(dirty.glob('*.tar.gz'))) as archive:
            result['dirty_sdist'] = sorted(member.name.split('/', 1)[1] for member in archive.getmembers() if member.isfile() and '/' in member.name)

        # what build does: the sdist, and then the wheel, from the sdist
        tree = copy_of_the_repository(work / 'build', checksum)
        sdists = work / 'sdists'
        sdists.mkdir()
        for name in ('get_requires_for_build_sdist', 'build_sdist'):
            hook(tree, name, sdists)
        sdist = next(sdists.glob('*.tar.gz'))
        with tarfile.open(sdist) as archive:
            result['sdist'] = sorted(member.name.split('/', 1)[1] for member in archive.getmembers() if member.isfile() and '/' in member.name)
            archive.extractall(work / 'unpacked')
        unpacked = next((work / 'unpacked').iterdir())
        for name in ('get_requires_for_build_wheel', 'build_wheel'):
            hook(unpacked, name, work / 'from_sdist', label='(from the sdist) ')
        with zipfile.ZipFile(next((work / 'from_sdist').glob('*.whl'))) as archive:
            result['wheel_from_sdist'] = {info.filename: (info.external_attr >> 16) & 0o111 for info in archive.infolist()}
        return result
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_how_many_times_enbid_is_built_by_each_hook():
    # only the hooks that build the wheel build EnBiD, once: those that ask what is needed, or what the package
    # is, or make the sdist, which is not built, do not
    assert flows()['builds'] == {
        'get_requires_for_build_wheel': 0,
        'prepare_metadata_for_build_wheel': 0,
        'build_wheel': 1,
        'get_requires_for_build_sdist': 0,
        'build_sdist': 0,
        '(from the sdist) get_requires_for_build_wheel': 0,
        '(from the sdist) build_wheel': 1,
        '(in a tree that built EnBiD) build_sdist': 0,
    }


def test_the_wheel_holds_the_executables_of_enbid_and_they_are_executable():
    wheel = flows()['wheel']
    for name in EXECUTABLES:
        assert wheel.get(f"enbid_ananke/Enbid-2.0/{name}"), f"{name} is missing from the wheel or not executable"


def test_the_wheel_holds_all_of_the_folder_of_enbid_and_the_licenses():
    # what is in the folders at any depth, as it was when the files were listed by walking them
    wheel = flows()['wheel']
    for name in ('Enbid-2.0/README', 'Enbid-2.0/src/Makefile', 'Enbid-2.0/src/main.cpp', '__license__/LICENSE'):
        assert f"enbid_ananke/{name}" in wheel, f"{name} is missing from the wheel"


def test_the_wheel_made_from_the_sdist_holds_what_the_wheel_made_from_the_tree_does():
    # this is how a release is built: the sdist, and the wheel from it, which has to make the executables itself
    def files(wheel):
        return {name: mode for name, mode in wheel.items() if '.dist-info/' not in name}
    assert files(flows()['wheel_from_sdist']) == files(flows()['wheel'])


def test_the_sdist_holds_nothing_of_enbid_and_what_building_from_it_needs():
    sdist = flows()['sdist']
    assert not [name for name in sdist if 'Enbid-2.0' in name]              # EnBiD is downloaded when it is built
    assert 'src/_build_utils.py' in sdist and 'setup.py' in sdist           # what building from it needs


def test_the_sdist_of_a_tree_that_has_built_enbid_holds_nothing_of_it_either():
    assert not [name for name in flows()['dirty_sdist'] if 'Enbid-2.0' in name]


def test_files_without_any_git_information_can_be_built_and_the_package_imported():
    # an archive of a commit that no tag names, a copy of the files without .git, as a Docker image is built from: versioneer
    # knows neither the version nor the date there ("0+unknown", None), and the metadata of the package used to need a date
    check_building_is_possible()
    work = pathlib.Path(tempfile.mkdtemp(prefix='enbid_ananke_no_git_'))
    try:
        site = work / 'site'
        site.mkdir()
        (site / 'sitecustomize.py').write_text(SITECUSTOMIZE)
        toy = toy_tarball()
        (work / 'toy.tar.gz').write_bytes(toy)
        # GIT_CEILING_DIRECTORIES: git does not look for a repository above the copy, as it would in a temporary folder that is in one
        environment = dict(without_git_variables(dict(os.environ)), PYTHONPATH=str(site), ENBID_TOY_TARBALL=str(work / 'toy.tar.gz'),
                           COUNTER=str(work / 'counter'), GIT_CEILING_DIRECTORIES=str(work))
        tree = copy_of_the_repository(work / 'plain', hashlib.sha256(toy).hexdigest(), with_git=False)
        assert not (tree / '.git').exists()
        wheels = work / 'wheels'
        wheels.mkdir()
        run_hook(tree, environment, 'build_wheel', wheels)
        installed = work / 'installed'
        with zipfile.ZipFile(next(wheels.glob('*.whl'))) as archive:
            archive.extractall(installed)
        result = subprocess.run([sys.executable, '-c', 'import enbid_ananke as e; print(e.__version__, e.__date__.year)'],
                                cwd=str(installed), env=dict(without_git_variables(dict(os.environ)), PYTHONPATH=str(installed)),
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr[-2000:]
        version, year = result.stdout.split()
        assert version == '0+unknown' and int(year) >= 2026
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    pass
