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
Check the distributions that `python -m build` made, before anyone publishes them.

    python .github/scripts/check_dist.py dist

The point of the wheel is to carry the EnBiD executables that setup.py compiled,
so a wheel without them (or with them not executable) is broken however well it
installs. The sdist has to carry what building from it needs: setup.py imports
src/_build_utils.py, which MANIFEST.in is what includes.
"""
import sys
import tarfile
import zipfile
from pathlib import Path

PACKAGE = "enbid_ananke"
ENBID_DIR = f"{PACKAGE}/Enbid-2.0"
EXECUTABLES = [f"{ENBID_DIR}/Enbid.3d", f"{ENBID_DIR}/Enbid.6d"]

WHEEL_REQUIRED = [
    f"{PACKAGE}/__init__.py",
    f"{PACKAGE}/_version.py",
    f"{PACKAGE}/__license__/LICENSE",
    *EXECUTABLES,
]
SDIST_REQUIRED = [  # relative to the directory the sdist unpacks into
    "setup.py",
    "README.md",
    "src/_build_utils.py",
    f"src/{PACKAGE}/__init__.py",
    f"src/{ENBID_DIR}/src/Makefile",
]


def check_wheel(path):
    problems = []
    with zipfile.ZipFile(path) as wheel:
        infos = {info.filename: info for info in wheel.infolist()}
    for name in WHEEL_REQUIRED:
        if name not in infos:
            problems.append(f"{path.name}: missing {name}")
    for name in EXECUTABLES:
        if name in infos and not (infos[name].external_attr >> 16) & 0o111:
            problems.append(f"{path.name}: {name} is not executable")
    if not any(n.startswith(f"{ENBID_DIR}/") and n.rsplit("/", 1)[-1] == "COPYING" for n in infos):
        print(f"::warning::{path.name}: EnBiD's COPYING is not in {ENBID_DIR}/")
    return problems


def check_sdist(path):
    problems = []
    with tarfile.open(path) as sdist:
        # the first path component is the directory it unpacks into
        names = {n.split("/", 1)[1] for n in sdist.getnames() if "/" in n}
    for name in SDIST_REQUIRED:
        if name not in names:
            problems.append(f"{path.name}: missing {name}")
    return problems


def main(argv):
    dist = Path(argv[1] if len(argv) > 1 else "dist")
    wheels, sdists = sorted(dist.glob("*.whl")), sorted(dist.glob("*.tar.gz"))
    problems = []
    if len(wheels) != 1 or len(sdists) != 1:
        problems.append(f"expected one wheel and one sdist in {dist}/, found "
                        f"{[p.name for p in wheels]} and {[p.name for p in sdists]}")
    else:
        problems += check_wheel(wheels[0]) + check_sdist(sdists[0])
    for problem in problems:
        print(f"::error::{problem}")
    if not problems:
        print(f"OK: {wheels[0].name} and {sdists[0].name} have what they should.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
