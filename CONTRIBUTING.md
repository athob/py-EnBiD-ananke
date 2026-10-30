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
- **install**: for each Python version from 3.8 to 3.15, installs the package and
  runs `pytest src`. The Python 3.12 run also reports the test coverage, in the
  summary of the run.
- **package**: builds the sdist and the wheel the way a release would, then runs
  `twine check --strict` and `.github/scripts/check_dist.py`: the EnBiD executables
  have to be in the wheel, and be executable.
- **docs**: builds the documentation, as Read the Docs does.
- **promote**: on a push to `develop`, once all the jobs above have passed, moves `stable`
  forward to that commit.

Apart from CI, two workflows report to Security > Code scanning: **CodeQL** (code
scanning; on `develop`, on pull requests and every Wednesday) and **Scorecard**
(the [OpenSSF](https://securityscorecards.dev) grading of the repository's
supply-chain habits; from `main`, every Thursday). Their findings are meant to be
looked at, and `stable` does not wait for them.

The tools the workflows install (ruff, pytest, build and twine, the documentation tools, and
what the CD workflow builds with) are locked with hashes in
[`.github/requirements/`](.github/requirements): each `requirements-X.in` says what is
wanted, and `requirements-X.txt` pins every package, transitive ones included, to a version
and to the hashes of its files, which `pip install --require-hashes` then insists on.
Dependabot proposes updates to the locks, by running again the `uv pip compile` command a
lock records in its header (which is why `dependabot.yml` says `uv`, not `pip`: pip-tools
would resolve for one Python only). It takes one version of each package as the current one,
and checks that the newest can be pinned for every Python the lock covers, so it cannot
maintain a lock that holds a package once per Python. The test tools are therefore locked
twice. `requirements-test.txt` covers the Pythons that are still supported (3.11 and up),
and is maintained by Dependabot. `requirements-frozen/requirements-test.txt` is a complete
lock of every Python from the oldest the package supports (3.8) up, used by the ones at the
end of their life (3.8 to 3.10). It is next to `requirements/` and not in it, because
Dependabot fetches the subfolders of its folder too. Because it is complete, retiring a
Python to it never touches it: raise the `--python-version` of the test lock in `update.sh`,
add that Python to the matrix of `ci.yml` (the tests check that both agree), and run
`update.sh`. Never copy the live lock into `requirements-frozen/`, which would lose the
entries of the older Pythons (the tests catch that too). `update.sh --upgrade` refreshes the
frozen lock when that is worth it, and uv gives each Python the newest version it supports.
To change a lock by hand, edit the `.in` file and run
`bash .github/requirements/update.sh` (add `--upgrade` to move everything to the newest
versions; it needs [uv](https://docs.astral.sh/uv/)), then commit the `.txt` files it wrote.
The same script writes the checksum the actionlint download is checked against: run it
again whenever `ACTIONLINT_VERSION` changes in `ci.yml`.

Scorecard also lists a few findings that are accepted rather than fixed, each for a reason:

- **Code-Review**: there is one maintainer, so nobody else is there to review a change.
- **Fuzzing**: the package is a thin wrapper, and the C++ it builds, EnBiD, is third-party.
- **Pinned-Dependencies, the `pip install .` lines of `ci.yml`**: they install this
  repository itself, which cannot be pinned by hash.
- **Vulnerabilities, pytest in the frozen test lock**:
  [PYSEC-2026-1845](https://osv.dev/PYSEC-2026-1845) (CVE-2025-71176, GHSA-6w46-j5rx-g56g)
  affects every pytest before 9.0.3, which needs Python 3.10 or later, so the lock for Python
  3.8 and 3.9 cannot have the fix.
  It only matters when the tests run on a machine shared with other users (it is about
  pytest's temporary directories in `/tmp`), and it goes away with the support of those
  Pythons.

An alert is identified by the place it is raised at, so a dismissed one comes back as a new
alert when a change moves its line. Check the list of open alerts first, then dismiss the
`pip install .` ones again with:

```bash
gh api "repos/athob/py-EnBiD-ananke/code-scanning/alerts?state=open&per_page=100" \
  --jq '.[] | select(.rule.id == "PinnedDependenciesID") | .number' | while read -r n; do
  gh api -X PATCH "repos/athob/py-EnBiD-ananke/code-scanning/alerts/$n" -f state=dismissed \
    -f dismissed_reason="won't fix" \
    -f dismissed_comment="Installs this repository itself, which cannot be pinned by hash."
done
```

Dependabot raises the same pytest advisory as an alert of its own, against the frozen lock.
Dismiss it as a tolerable risk, so that it does not try to open a security update for a lock
that cannot take one:

```bash
gh api -X PATCH repos/athob/py-EnBiD-ananke/dependabot/alerts/1 -f state=dismissed \
  -f dismissed_reason=tolerable_risk \
  -f dismissed_comment="Test-time only. The fix needs Python 3.10 or later: see CONTRIBUTING.md."
```

If CI fails on one Python version only, it is usually a real incompatibility
rather than bad luck.

## Conventions

- **Supported Pythons** are the ones in `python_requires` in `setup.py`
  (currently 3.8 up to 3.15). CI covers all of them, and the classifiers in
  `src/enbid_ananke/__metadata__.py` name them for PyPI: the tests check that the three agree.
- **Do not edit `versioneer.py` or `src/enbid_ananke/_version.py` by hand.**
  They are generated by [versioneer](https://github.com/python-versioneer/python-versioneer),
  configured in `setup.cfg`.
- **New behaviour comes with a test** in `src/tests`. The tests do not compile EnBiD: they use a
  stand-in, `with_fake_enbid` in `src/tests/utils.py`, that reads the parameter file and writes
  the output files like the real one, with densities made up from the input (1, 2, 3... without
  masses, ten times the mass with masses), so that what `enbid` returns can be checked against
  what went in. A test that changes `CONSTANTS` has to put it back (`preserved_enbid_paths`). A
  weakness that is known and not fixed yet is a test marked `xfail(strict=True)` with its reason:
  it fails the day the weakness is fixed, which is the day to remove the mark.
  `src/tests/test_integration.py` is the exception: it runs `enbid` with the real EnBiD, when the
  executables are built (installing the package builds them), and is skipped otherwise.
- **The repository checks itself**: `src/tests/test_repository.py` verifies, among other
  things, that the DOIs and the license wording agree between the README, `CITATION.cff`,
  `.zenodo.json` and the metadata, that the actions are pinned and the workflows set their
  permissions, that what they install is locked with hashes, and that the changelog has its
  format. If you change one of those, it tells you what else needs to follow.
- **A change a user would notice gets a line in `CHANGELOG.md`**, under
  `[Unreleased]`, in the matching group (Added, Changed, Deprecated, Removed,
  Fixed or Security). The release moves those lines under the new version.

## Versioning

The package version is not written down anywhere in the source: versioneer
derives it from the git tags, which start with `v` (`v0.3.3`). Version numbers
follow [Semantic Versioning](https://semver.org/). The major number is still `0`,
although the package has long been marked Production/Stable on PyPI, and a `1.0.0`
release is planned. Until then Semantic Versioning still lets a minor version change
the interface, and the changelog says so when one does (as it did for 0.3.0).
Pre-releases are written the Python way
([PEP 440](https://peps.python.org/pep-0440/)): `v0.3.4a1`, `v0.3.4b1`, `v0.3.4rc0`,
`v0.3.4.dev1`.

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
