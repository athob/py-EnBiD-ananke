# Contributing to py-EnBiD-ananke

Thanks for helping out! This page is the short version of "how work gets into
py-EnBiD-ananke": the branches, how to set up a development copy, what the
automatic checks do, and how versions and releases work. Everyone taking part is
expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

py-EnBiD-ananke is the wrapper [py-ananke](https://github.com/athob/py-ananke)
uses to run EnBiD, so a change to a function's signature or behaviour can break
py-ananke. If you plan something like that, open an issue first so it can be
discussed.

## The branches

| Branch    | What it is                                                         | Who writes to it                              |
|-----------|--------------------------------------------------------------------|-----------------------------------------------|
| `main`    | The latest **release**.                                            | The maintainer, when releasing.               |
| `stable`  | The newest development state that passed the automatic checks.     | **Only CI** -- never commit to it by hand.    |
| `develop` | Where development happens; every other branch starts from it.      | The maintainer, and merged pull requests.     |

Everything else (`my-feature`, `fix-something`, ...) is a short-lived branch
created from `develop`. When the checks pass on a push to `develop`, CI merges
`develop` into `stable` by itself.

## Making a change

1. Branch from `develop`: `git switch develop && git pull && git switch -c my-change`.
2. Make the change, with a test for it in `src/tests`.
3. Run the checks locally (next section).
4. Open a pull request into `develop`. Keep a pull request about one thing.

## Setting up

```bash
git clone https://github.com/athob/py-EnBiD-ananke
cd py-EnBiD-ananke
git switch develop
python -m venv .venv && source .venv/bin/activate      # or a conda environment
pip install .
pip install pytest ruff
```

`pip install .` downloads the EnBiD source (from SourceForge), compiles it and
installs the executable with the package, so it needs network access, `tar`,
GNU make and g++, and Windows is not supported. The tests import the package
straight from `src/` (they use relative imports), so once the install has worked
your edits are picked up without installing again. The version is read from the
git tags (see "Versioning" below), so work from a clone that has them:
`git fetch --tags` if you cloned a fork.

Before you push, run what CI runs:

```bash
ruff check .      # must pass
pytest src
```

To have ruff run on every commit by itself, install the optional
[pre-commit](https://pre-commit.com/) hook: `pip install pre-commit && pre-commit install`.

## The automatic checks (CI)

The **CI** workflow ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs on
every push to a branch other than `main` and `stable`, on pull requests from forks
into `develop`, every Monday (to notice new releases of the dependencies, or trouble
downloading EnBiD, before anyone else does) and on demand from the Actions tab. Its
jobs:

- **lint**: [ruff](https://docs.astral.sh/ruff/). Only the serious findings fail it
  (syntax errors and undefined names, selected in `pyproject.toml`); the style
  warnings are listed for information.
- **workflows**: [actionlint](https://github.com/rhysd/actionlint) on the workflow
  files. You can run it locally too, and the pre-commit hook does so when it is
  installed.
- **install**: for each Python version from 3.8 to 3.14, installs the package and
  runs `pytest src`. The Python 3.12 run also reports the test coverage, in the
  summary of the run.
- **package**: builds the sdist and the wheel the way a release would, then runs
  `twine check --strict` and `.github/scripts/check_dist.py`: the EnBiD executables
  have to be in the wheel, and be executable.
- **docs**: builds the documentation, as Read the Docs does. For now it is only
  informative: a failure shows up in red, but does not stop `stable` from moving.
- **promote**: on a push to `develop`, once lint, workflows, install and package have
  passed, moves `stable` forward to that commit.

Apart from CI, two workflows report to Security > Code scanning: **CodeQL** (code
scanning; on `develop`, on pull requests and every Wednesday) and **Scorecard**
(the [OpenSSF](https://securityscorecards.dev) grading of the repository's
supply-chain habits; from `main`, every Thursday). Their findings are meant to be
looked at, and `stable` does not wait for them.

The tools the workflows install (ruff, pytest, build and twine, the documentation tools,
and what the CD workflow builds with) are locked with hashes in
[`.github/requirements/`](.github/requirements): each `requirements-X.in` says what is
wanted, and `requirements-X.txt` pins every package, transitive ones included, to a version
and to the hashes of its files, which `pip install --require-hashes` then insists on.
Dependabot proposes updates to the locks. To change one by hand, edit the `.in` file and run
`bash .github/requirements/update.sh` (add `--upgrade` to move everything to the newest
versions; it needs [uv](https://docs.astral.sh/uv/)), then commit the `.txt` files it wrote.

If CI fails on one Python version only, it is usually a real incompatibility
rather than bad luck.

## Conventions

- **Supported Pythons** are the ones in `python_requires` in `setup.py`
  (currently 3.8 up to 3.14). CI covers all of them.
- **Do not edit `versioneer.py` or `src/enbid_ananke/_version.py` by hand.**
  They are generated by [versioneer](https://github.com/python-versioneer/python-versioneer),
  configured in `setup.cfg`.
- **New behaviour comes with a test** in `src/tests`.
- **The repository checks itself**: `src/tests/test_repository.py` verifies, among other
  things, that the DOIs and the license wording agree between the README, `CITATION.cff`,
  `.zenodo.json` and the metadata, that the actions are pinned and the workflows set their
  permissions, and that the changelog has its format. If you change one of those, it tells
  you what else needs to follow.
- **A change a user would notice gets a line in `CHANGELOG.md`**, under
  `[Unreleased]`, in the matching group (Added, Changed, Deprecated, Removed,
  Fixed or Security). The release moves those lines under the new version.

## Versioning

The package version is not written down anywhere in the source: versioneer
derives it from the git tags, which start with `v` (`v0.3.3`). Version numbers
follow [Semantic Versioning](https://semver.org/), and while the major number is
`0` anything may change between minor versions. Pre-releases are written the
Python way ([PEP 440](https://peps.python.org/pep-0440/)): `v0.3.4a1`,
`v0.3.4b1`, `v0.3.4rc0`, `v0.3.4.dev1`.

## Releasing (maintainer)

Pushing a tag that starts with `v` runs the **CD** workflow
([`.github/workflows/cd.yml`](.github/workflows/cd.yml)), which publishes to TestPyPI
and PyPI. What the tags may look like, and the steps, are in
[`RELEASING.md`](RELEASING.md).

## Questions and bug reports

Security problems are the exception: report them privately, as
[`SECURITY.md`](SECURITY.md) describes. For anything else, open an issue; the
templates ask for what is needed to reproduce it.

By contributing you agree that your contribution is licensed under the
project's license, the GNU General Public License, version 2 or (at your option)
any later version (see `LICENSE` and `COPYRIGHT`).
