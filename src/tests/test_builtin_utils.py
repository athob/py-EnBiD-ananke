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
Tests of the version of a command and of the import of a source file, from the built-in utilities.
The commands are fakes (fake_commands in utils.py), so that the versions they print are known.
"""
import subprocess
import sys
from unittest import mock

import pytest

from ..enbid_ananke._builtin_utils import get_version_of_command, import_source_file
from .utils import in_tmp_wd, fake_commands


@pytest.mark.parametrize('output, version', [
    ('GNU Make 4.3\nBuilt for x86_64-pc-linux-gnu', '4.3'),
    ('g++ (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0', '11.4.0'),          # the first of the numbers: not 22.04
    ('tar (GNU tar) 1.34', '1.34'),
    ("it's a tool's version 5.2", '5.2'),                              # quotes are not a problem
    ('version 2.7.18.1 (build 5.3)', '2.7.18.1'),
])
def test_the_version_is_the_first_dotted_number_of_the_output(output, version):
    with fake_commands({'tool': output}):
        assert get_version_of_command('tool') == version


def test_an_output_without_a_version_is_an_index_error():
    # Not a friendly error, but the one there is: the callers only expect FileNotFoundError.
    with fake_commands({'tool': 'no number here'}):
        with pytest.raises(IndexError):
            get_version_of_command('tool')


def test_a_command_that_is_not_there_is_a_file_not_found_error():
    with fake_commands({}):
        with pytest.raises(FileNotFoundError):
            get_version_of_command('tool')


def test_a_command_that_fails_raises():
    with fake_commands({'tool': ('1.0', 4)}):                            # it prints a version, then exits with an error
        with pytest.raises(subprocess.CalledProcessError):
            get_version_of_command('tool')


@in_tmp_wd
def test_a_source_file_is_imported_as_the_module_of_that_name():
    with open('mine.py', 'w') as f:
        f.write('VALUE = 42\ndef double(x):\n    return 2 * x\n')
    try:
        module = import_source_file('a_module_made_for_this_test', 'mine.py')
        assert module.VALUE == 42 and module.double(4) == 8
        assert sys.modules['a_module_made_for_this_test'] is module
    finally:
        sys.modules.pop('a_module_made_for_this_test', None)


@in_tmp_wd
def test_importing_a_source_file_again_reads_it_again():
    # Python trusts the bytecode it cached for a file whose size and modification time (to the second) are those
    # it was made from, and the two versions of this file are written within the same second and have the same
    # size: no bytecode is written here, so that what is tested is the function, not that cache.
    try:
        with mock.patch.object(sys, 'dont_write_bytecode', True):
            with open('mine.py', 'w') as f:
                f.write('VALUE = 1\n')
            assert import_source_file('a_module_made_for_this_test', 'mine.py').VALUE == 1
            with open('mine.py', 'w') as f:
                f.write('VALUE = 2\n')
            assert import_source_file('a_module_made_for_this_test', 'mine.py').VALUE == 2
    finally:
        sys.modules.pop('a_module_made_for_this_test', None)


@in_tmp_wd
def test_a_source_file_that_does_not_exist_is_a_file_not_found_error():
    with pytest.raises(FileNotFoundError):
        import_source_file('a_module_made_for_this_test', 'nothing here.py')


if __name__ == '__main__':
    pass
