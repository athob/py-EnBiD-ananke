# Changelog

All notable changes to py-EnBiD-ananke are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
the project follows [Semantic Versioning](https://semver.org/) as far as `0.x` allows:
anything may change between minor versions. A section is written for every release
when it is made; those below were written afterwards, from the release notes and the
history. Versions before 0.2.0 were pre-releases: see their tags and release notes on
[GitHub](https://github.com/athob/py-EnBiD-ananke/releases).

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
- CodeQL code scanning of the Python source, and the OpenSSF Scorecard of the repository.
- A releasing guide. The CD workflow checks that `CHANGELOG.md` has the dated section of a
  release before building anything, and creates the GitHub release from that section.

### Changed

- `write_for_enbid` writes its files inside a subfolder of `name`, named after the first
  16 hexadecimal characters of the SHA-256 digest of the input data.
- The source file headers say GPL v2.0 or later (GPL-2.0-or-later), as EnBiD's own
  copyright notice does.
- The `CI/CD` workflow is now two: `CI` and `CD`. `stable` is moved forward to a commit
  that passed CI by a fast-forward, the actions are pinned to commit SHAs, and the
  workflows only get the permissions they need.

### Fixed

- The Read the Docs build, which the renamed example notebook had broken.

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
