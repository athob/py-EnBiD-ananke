# Changelog

All notable changes to py-EnBiD-ananke are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
the project follows [Semantic Versioning](https://semver.org/). The major number is
still `0`, so a minor version can still change the interface; a `1.0.0` release is
planned. A section is written for every release
when it is made; those below were written afterwards, from the release notes and the
history. The package did not start with 0.2.0: it had been in development since March
2022, in pre-releases that are summarized at the bottom, under
[Before 0.2.0](#before-020).

## [Unreleased]

### Added

- Development versions: a tag such as `v0.3.4.dev0` publishes to TestPyPI only, and the
  CD workflow now refuses a tag that is not a plain PEP 440 version.
- Project files: a contributing guide, a code of conduct, a security policy, issue
  forms and a pull request template, an editorconfig, a pre-commit configuration, a
  markdownlint configuration, and Dependabot for the GitHub Actions.
- `CITATION.cff`, with the py-ananke article as the preferred citation, the Zenodo
  record of this package, and EnBiD. The Zenodo record now points back to the article.
- Checks in CI: ruff, actionlint, a test coverage report in the job summary, a build
  and check of the sdist and the wheel, and a build of the documentation. CI also runs
  on pull requests, every week and on demand.
- A README that gives the installation requirements and says how to cite the package.
- The OpenSSF Best Practices badge, shown in the README. The entry is in progress: the passing
  level is not reached yet.
- The trove classifiers of PyPI name each supported Python version, 3.8 to 3.15.
- Python 3.15 is supported, and tested by CI.
- CodeQL code scanning of the Python source, and the OpenSSF Scorecard of the repository.
- Tests of the repository files (the DOIs and the license wording agree, the actions are pinned,
  the changelog has its format) and of the release script.
- Tests of every public function of the package, run against a stand-in for EnBiD: the GADGET
  files it writes and reads, the hash of the input, the parameter file and its keywords, the
  choice of the 3D or 6D executable, the caching, and `enbid` from end to end.
- Tests of the tools that build EnBiD when the package is installed (the check of the system,
  the download, the configuring of the Makefile, the build, the package data), without a
  network or a compiler, and of the version of a command.
- The test coverage is measured by branch too, without the footer of the modules of the package
  that no test can run, and it has a floor of 95%: the Python 3.12 run of CI fails under it.
- Tests of `enbid` with the real EnBiD, run when it is built (installing the package builds it):
  one finite density per particle, the same answer for the same input, no change when the data
  is moved as a whole, and a density that falls with the distance from the center of a cloud.
- The CD workflow can be run by hand: it builds the distributions and publishes nothing.
- A releasing guide. The CD workflow checks that `CHANGELOG.md` has the dated section of a
  release before building anything, and creates the GitHub release from that section.

### Changed

- `write_for_enbid` writes its files inside a subfolder of `name`, named after the first
  16 hexadecimal characters of the SHA-256 digest of the input data.
- The source file headers say GPL v2.0 or later (GPL-2.0-or-later), as EnBiD's own
  copyright notice does.
- The tools the CI and CD workflows install are locked with hashes, in
  `.github/requirements/`: a tool cannot change under a run, and a release is built with
  tools whose hashes were checked.
- The `CI/CD` workflow is now two: `CI` and `CD`. `stable` is moved forward to a commit
  that passed CI by a fast-forward, the actions are pinned to commit SHAs, and the
  workflows only get the permissions they need.
- The CD workflow builds with Python 3.12 inside its container, Python 3.10 having reached
  its end of life.

### Fixed

- The Read the Docs build, which the renamed example notebook had broken.
- Importing the package no longer prints a `SyntaxWarning` about invalid escape sequences on
  recent Pythons: two regular expressions are now raw strings. Nothing else about them changes.

## [0.3.3] - 2026-08-10

### Added

- Support for the 6D implementation of EnBiD next to the 3D one: both executables
  (`Enbid.3d` and `Enbid.6d`) are built when the package is installed.
- The input masses can be used as weights.

### Changed

- The pipeline computes a mass density rather than a number density, and reads and
  writes GADGET formatted data instead of ASCII.
- `make clean` is run as part of building EnBiD at installation.

## [0.3.2] - 2026-04-14

### Added

- A `COPYRIGHT` file, and copyright notices in all the source files.
- `pyproject.toml`, which declares the build requirements.
- A GitHub Actions workflow that publishes to TestPyPI and PyPI, building the wheel in a
  manylinux container and repairing it with auditwheel. For release candidates it waits
  for the CI run of the tagged commit.

### Changed

- A wider range of dependency versions is accepted.

### Fixed

- The module name in the docstrings.

## [0.3.1] - 2025-06-28

### Added

- The installation stops with an error on Windows, which is not supported.
- Instructions to install from PyPI, in the README.

### Changed

- The setup no longer calls `ext_modules`, and the wheels are generated for a wider
  `manylinux` standard.

## [0.3.0] - 2025-06-05

### Changed

- **Breaking:** the module has a new name, `enbid_ananke`, in lower case to comply with
  [PEP 8](https://peps.python.org/pep-0008/): imports have to be updated.
- The build was reworked to work with versioneer, in particular for building tarballs.

## [0.2.1] - 2025-05-28

### Added

- Caching: EnBiD can "checkpoint" its run, reusing the output of a previous run of the
  same input, which is recognized by a hash of the data.
- Python 3.12 and 3.13 are supported.

## [0.2.0.post2] - 2024-10-16

### Changed

- The Zenodo metadata (`.zenodo.json`).

## [0.2.0.post1] - 2024-10-16

### Changed

- The Zenodo metadata (`.zenodo.json`).

## [0.2.0.post0] - 2024-10-16

### Changed

- The README.

## [0.2.0] - 2024-10-15

### Added

- The documentation, built with Sphinx and hosted on Read the Docs.
- A check that the system has what building EnBiD needs, before it is attempted.

### Changed

- The version is now derived from the git tags by versioneer.

## Before 0.2.0

py-EnBiD-ananke was in development long before 0.2.0: the repository dates from March
2022, and the versions below are pre-releases, tagged while the package was taking shape
and not documented as they were made. What follows is a rough history, put together
afterwards from the commit history: the dates are those of the tagged commits, and the
descriptions are far from exhaustive. By December 2022 the work was already organized
around the `develop`, `main` and `stable` branches, as it still is.

### Alpha versions, 2022-2023

- `v0.0.0-alpha`, 2022-06-02: the first implementation of the wrapper, with an example
  notebook.
- `v0.0.1-alpha`, 2022-12-14: `pathlib` in place of `os`, the constants in a module of
  their own, an `ngb` argument added to the `enbid` function and tidier dependencies in
  `setup.py` (all from June 2022), then updates to the README and the metadata.
- `v0.0.2-alpha`, 2023-02-15: docstrings, a fix of the package installation, and a
  warning against a potential cause of a C++ segmentation fault.
- `v0.0.3-alpha`, 2023-03-21: attempts at fixing an issue with `/dev/tty`.
- `v0.1.0-alpha`, 2023-04-07, and `v0.1.1-alpha`, 2023-04-12: a change of name, and the
  repository URL that goes with it.
- `v0.1.2-alpha`, 2023-07-02: a choice of the type of kernel, and more control over the
  parameters in EnBiD's parameter file.

### Beta versions, 2023-2024

- `v0.1.2-beta`, 2023-08-25: a more accurate requirement on the Python version, and the
  move to beta versioning.
- `v0.1.2-beta2`, 2023-08-29: the first GitHub Actions workflow, with the unsupported
  Python versions removed from it.
- `v0.1.3-beta`, 2023-11-23: a `utils.py` module, an improved parameter file template and
  documentation, a fix for data that is not centered, flake8 linting in the workflow, a
  `CONSTANTS` singleton so that some constants can be changed on the fly, a verbose
  option that controls the output of the subprocess, and the first tests.
- `v0.2.0-beta`, 2024-08-16, and `v0.2.0-beta2`, 2024-08-21: the first Sphinx
  documentation, on Read the Docs.
- `v0.2.0b3`, 2024-09-01: versioneer added.

Nothing was tagged between `v0.1.3-beta` (November 2023) and `v0.2.0-beta` (August 2024),
but the work went on: the commits of those months pin the versions of the dependencies,
use `setuptools` in place of `distutils`, reorganize the metadata, the constants and the
utilities, revise the way the particles are centered on the most clustered structure in
the data, and start the caching work, which was released in 0.2.1.

[Unreleased]: https://github.com/athob/py-EnBiD-ananke/compare/v0.3.3...develop
[0.3.3]: https://github.com/athob/py-EnBiD-ananke/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/athob/py-EnBiD-ananke/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/athob/py-EnBiD-ananke/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/athob/py-EnBiD-ananke/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/athob/py-EnBiD-ananke/compare/v0.2.0.post2...v0.2.1
[0.2.0.post2]: https://github.com/athob/py-EnBiD-ananke/compare/v0.2.0.post1...v0.2.0.post2
[0.2.0.post1]: https://github.com/athob/py-EnBiD-ananke/compare/v0.2.0.post0...v0.2.0.post1
[0.2.0.post0]: https://github.com/athob/py-EnBiD-ananke/compare/v0.2.0...v0.2.0.post0
[0.2.0]: https://github.com/athob/py-EnBiD-ananke/compare/v0.1.3-beta...v0.2.0
