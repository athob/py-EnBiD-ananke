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
Tests of the repository itself rather than of the code: the project files are there,
what has to agree with something else does (the DOIs, the license wording), the
workflows keep the habits they were given, the changelog has its format. Standard
library only, and nothing here needs EnBiD.
"""
import json
import pathlib
import re
import warnings

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))

ZENODO_DOI = "10.5281/zenodo.13937082"   # all versions of this package
JOSS_DOI = "10.21105/joss.06234"         # the py-ananke article
OPENSSF_PROJECT = "15711"                # the OpenSSF Best Practices badge entry


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


@pytest.mark.parametrize("path", [
    "README.md", "LICENSE", "COPYRIGHT", "CHANGELOG.md", "CONTRIBUTING.md", "RELEASING.md",
    "CODE_OF_CONDUCT.md", "SECURITY.md", "CITATION.cff", ".zenodo.json", ".editorconfig",
    ".gitattributes", ".pre-commit-config.yaml", ".markdownlint.yaml", ".readthedocs.yaml",
    ".github/dependabot.yml", ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml", ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
])
def test_project_file_exists(path):
    assert (ROOT / path).is_file(), f"{path} is missing"


def test_gitattributes_keeps_versioneer_export_subst():
    # versioneer needs this to find the version in a `git archive`
    assert "src/enbid_ananke/_version.py export-subst" in read(".gitattributes")


# -- the workflows -----------------------------------------------------------------

def test_there_are_workflows():
    assert {p.name for p in WORKFLOWS} >= {"ci.yml", "cd.yml"}


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_actions_are_pinned_to_a_commit(workflow):
    unpinned = []
    for line in workflow.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*(?:-\s+)?uses:\s+(?P<action>[^@\s]+)@(?P<ref>\S+)(?P<rest>.*)$", line)
        if match and not match.group("action").startswith("./"):
            if not re.fullmatch(r"[0-9a-f]{40}", match.group("ref")) or "#" not in match.group("rest"):
                unpinned.append(line.strip())
    assert not unpinned, f"{workflow.name}: pin to a commit SHA, with the version in a comment: {unpinned}"


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_workflows_set_their_permissions(workflow):
    text = workflow.read_text(encoding="utf-8")
    assert re.search(r"^permissions:", text, flags=re.MULTILINE), \
        f"{workflow.name} has no top-level `permissions:`: the token would get the repository default"


def test_promote_waits_for_every_other_job_of_ci():
    # a job added to ci.yml and forgotten in promote's needs would not hold stable back
    ci = read(".github/workflows/ci.yml")
    jobs = re.findall(r"^  ([a-z][\w-]*):\s*$", ci.split("\njobs:\n", 1)[1], flags=re.MULTILINE)
    needs = re.search(r"^  promote:.*?^    needs:\s*\[([^\]]*)\]", ci, flags=re.MULTILINE | re.DOTALL).group(1)
    assert set(jobs) - {"promote"} == {name.strip() for name in needs.split(",")}


def test_cd_publishes_only_on_a_push():
    # the workflow can also be run by hand, to try a build out: that must never publish anything
    cd = read(".github/workflows/cd.yml")
    jobs = dict(re.findall(r"^  ([a-z][\w-]*):\s*\n(.*?)(?=^  [a-z][\w-]*:\s*\n|\Z)",
                           cd.split("\njobs:\n", 1)[1], flags=re.MULTILINE | re.DOTALL))
    for name in ("publish-to-testpypi", "publish-to-pypi", "github-release"):
        condition = re.search(r"^    if:(.*)$", jobs[name], flags=re.MULTILINE)
        assert condition and "github.event_name == 'push'" in condition.group(1), \
            f"{name} has to run only on a push: a run by hand must not publish"


def test_the_cd_build_python_is_the_one_its_lock_is_compiled_for():
    # the build tools are locked for one Python: the container has to run that one
    python = re.search(r"/opt/python/cp(\d)(\d+)-cp\d+\S*/bin", read(".github/workflows/cd.yml"))
    header = "\n".join((REQUIREMENTS / "requirements-cd-build.txt").read_text(encoding="utf-8").splitlines()[:3])
    assert re.search(rf"--python-version\s+{python.group(1)}\.{python.group(2)}\b", header), \
        f"cd.yml builds with Python {python.group(1)}.{python.group(2)}: run .github/requirements/update.sh"


def test_cd_waits_for_a_workflow_that_exists():
    match = re.search(r'WORKFLOW_FILE="([^"]+)"', read(".github/workflows/cd.yml"))
    assert match, "the CD workflow no longer says which workflow it waits for"
    assert (ROOT / ".github" / "workflows" / match.group(1)).is_file()


REQUIREMENTS = ROOT / ".github" / "requirements"
# requirements-frozen/ holds the lock of the Pythons that are past their end of life. It is next to
# requirements/ and not in it: Dependabot fetches the subfolders of the folder it is given.
FROZEN = ROOT / ".github" / "requirements-frozen"
LOCKS = sorted(REQUIREMENTS.glob("requirements-*.txt")) + sorted(FROZEN.glob("requirements-*.txt"))
SOURCES = sorted(REQUIREMENTS.glob("requirements-*.in")) + sorted(FROZEN.glob("requirements-*.in"))


def test_pip_installs_in_workflows_are_pinned_by_hash():
    # installing this repository itself (`pip install .`) cannot be pinned by hash; any other
    # pip install has to be of a lock (see .github/requirements/update.sh)
    unpinned = []
    for workflow in WORKFLOWS:
        for number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("#", 1)[0].strip()
            if re.search(r"\bpip install\b", code) and "--require-hashes" not in code \
                    and not re.search(r"\bpip install \.$", code):
                unpinned.append(f"{workflow.name}:{number}: {code}")
    assert not unpinned, f"pip install without --require-hashes: {unpinned}"


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_workflows_install_locks_that_exist(workflow):
    # the names are found wherever they are written, in a command or in a matrix, relative to .github/
    text = workflow.read_text(encoding="utf-8")
    for lock in set(re.findall(r"requirements(?:-frozen)?/requirements-[\w.\-]+\.txt", text)):
        assert (ROOT / ".github" / lock).is_file(), f"{workflow.name} installs {lock}, which does not exist"


def test_dependabot_updates_the_locks_with_uv():
    # The pip ecosystem would regenerate a lock with pip-compile for its own Python only, and drop
    # what the other Pythons need: it broke the test lock. The uv ecosystem runs the lock's own
    # `uv pip compile` command again.
    text = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    entries = [e for e in re.split(r"^\s*- package-ecosystem:\s*", text, flags=re.MULTILINE)[1:]
               if re.search(r"^\s*directory:\s*/\.github/requirements\s*$", e, flags=re.MULTILINE)]
    assert len(entries) == 1, "dependabot.yml needs exactly one entry for /.github/requirements"
    assert entries[0].split()[0].strip("\"'") == "uv", "the locks must be updated by the uv ecosystem, not pip"


@pytest.mark.parametrize("lock", LOCKS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_locks_record_the_command_dependabot_runs_again(lock):
    header = "\n".join(lock.read_text(encoding="utf-8").splitlines()[:3])
    assert f"uv pip compile {lock.stem}.in" in header, f"{lock.name} does not record its uv pip compile command"
    for option in ("--universal", "--generate-hashes", "--python-version"):
        assert option in header, f"{lock.name} was not compiled with {option}: Dependabot would not keep it"


@pytest.mark.parametrize("lock", sorted(REQUIREMENTS.glob("requirements-*.txt")), ids=lambda p: p.name)
def test_locks_dependabot_maintains_pin_each_package_once(lock):
    # Dependabot takes one version as the current one and checks the newest can be pinned for
    # every Python the lock covers: a package locked once per Python is reported as an error.
    # Such a lock belongs in requirements-frozen/, which it does not scan.
    pins = [line for line in lock.read_text(encoding="utf-8").splitlines()
            if re.match(r"^[A-Za-z0-9_.\-]+(\[[^\]]*\])?==", line)]
    names = [re.match(r"^([A-Za-z0-9_.\-]+)", line).group(1).lower() for line in pins]
    twice = sorted({name for name in names if names.count(name) > 1})
    assert not twice, f"{lock.name} pins {twice} more than once: it cannot be maintained by Dependabot"


def test_the_folder_dependabot_scans_has_no_subfolders():
    # Dependabot fetches the subfolders of the folder it is given, not only its files: it found the
    # frozen lock in requirements/frozen/ and tried to bump its pins. A lock it must not maintain
    # lives next to the folder, as requirements-frozen/ does.
    subfolders = [p.name for p in REQUIREMENTS.iterdir() if p.is_dir() and p.name != "__pycache__"]
    assert not subfolders, f".github/requirements/ has subfolders {subfolders}: Dependabot would scan them"
    assert not re.search(r"directory:\s*/\.github/requirements-frozen",
                         (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))


def test_each_python_of_the_matrix_has_the_right_test_lock():
    # the Pythons below the one requirements-test.txt is compiled for use the frozen lock, the others do not
    ci = read(".github/workflows/ci.yml")
    versions = re.findall(r'"(3\.\d+)"', re.search(r"python-version:\s*\[([^\]]*)\]", ci).group(1))
    frozen = dict(re.findall(r'-\s*python-version:\s*"(3\.\d+)"\s*\n\s*test-lock:\s*(\S+)', ci))
    header = "\n".join((REQUIREMENTS / "requirements-test.txt").read_text(encoding="utf-8").splitlines()[:3])
    lowest = int(re.search(r"--python-version\s+3\.(\d+)", header).group(1))
    for version in versions:
        if int(version.split(".")[1]) < lowest:
            assert frozen.get(version) == "requirements-frozen/requirements-test.txt", \
                f"Python {version} needs the frozen lock"
        else:
            assert version not in frozen, f"Python {version} is covered by requirements-test.txt"


def test_the_frozen_lock_is_a_complete_lock():
    # Compiled with the oldest Python the package supports, it holds an answer for every Python
    # from there up: that is what lets a Python be retired to it without touching it, and what a
    # copy of the live lock (compiled for a newer Python) would lose.
    oldest = re.search(r"python_requires\s*=\s*['\"]>=3\.(\d+)", read("setup.py")).group(1)
    lock = FROZEN / "requirements-test.txt"
    header = "\n".join(lock.read_text(encoding="utf-8").splitlines()[:3])
    assert re.search(rf"--python-version\s+3\.{oldest}\b", header), \
        f"requirements-frozen/requirements-test.txt has to be compiled for Python 3.{oldest}, the oldest the package supports"


def requirement_names(path):
    """The names of the packages a requirements file asks for, the files it includes with -r too."""
    names = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("-r"):
            names |= requirement_names((path.parent / line[2:].strip()).resolve())
        elif line and not line.startswith("-"):
            names.add(re.sub(r"[-_.]+", "-", re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", line).group(0)).lower())
    return names


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_every_requirement_is_in_its_lock(source):
    # a requirement added to a .in file, and no run of update.sh after it, would leave the tools without it
    lock = source.with_suffix(".txt").read_text(encoding="utf-8")
    pinned = {re.sub(r"[-_.]+", "-", name).lower()
              for name in re.findall(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==", lock, flags=re.MULTILINE)}
    missing = sorted(requirement_names(source) - pinned)
    assert not missing, f"{source.name} asks for {missing}, which {source.with_suffix('.txt').name} does not pin: run update.sh"


def test_the_live_and_the_frozen_test_requirements_ask_for_the_same_tools():
    def tools(path):
        lines = path.read_text(encoding="utf-8").splitlines()
        return sorted(line.strip() for line in lines if line.strip() and not line.startswith("#"))
    assert tools(REQUIREMENTS / "requirements-test.in") == tools(FROZEN / "requirements-test.in")


def test_there_are_ci_requirements():
    assert SOURCES


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_ci_requirements_are_locked_with_hashes(source):
    lock = source.with_suffix(".txt")
    assert lock.is_file(), f"{lock.name} is missing: run .github/requirements/update.sh"
    pins = [line for line in lock.read_text(encoding="utf-8").splitlines()
            if re.match(r"^[A-Za-z0-9_.\-]+(\[[^\]]*\])?==", line)]
    assert pins, f"{lock.name} pins nothing"
    # every pin is followed by the hashes of its files, which is what the trailing backslash says
    assert all(line.rstrip().endswith("\\") for line in pins), f"a pin without hashes in {lock.name}"
    assert "--hash=sha256:" in lock.read_text(encoding="utf-8")


def test_the_actionlint_download_has_its_checksum():
    checksum = (REQUIREMENTS / "actionlint.sha256").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"[0-9a-f]{64}", checksum)


# -- what has to agree with something else ----------------------------------------

def test_the_dois_agree():
    metadata = re.search(r'^__doi__ = "([^"]+)"', read("src/enbid_ananke/__metadata__.py"), flags=re.MULTILINE)
    assert metadata and metadata.group(1) == JOSS_DOI
    cff = read("CITATION.cff")
    assert re.search(rf"^doi: {re.escape(ZENODO_DOI)}$", cff, flags=re.MULTILINE)
    assert re.search(rf"^  doi: {re.escape(JOSS_DOI)}$", cff, flags=re.MULTILINE)
    readme = read("README.md")
    assert ZENODO_DOI in readme and JOSS_DOI in readme
    related = json.loads(read(".zenodo.json"))["related_identifiers"]
    assert any(item["identifier"] == JOSS_DOI for item in related)


def test_the_openssf_badge_names_one_project_everywhere():
    pattern = re.compile(r"bestpractices\.dev/projects/(\d+)")
    readme = read("README.md")
    # the image and the page it opens are the same entry, and the other documents agree with it
    assert (f"(https://www.bestpractices.dev/projects/{OPENSSF_PROJECT}/badge)]"
            f"(https://www.bestpractices.dev/projects/{OPENSSF_PROJECT})") in readme
    assert set(pattern.findall(readme)) == {OPENSSF_PROJECT}
    for name in ("CONTRIBUTING.md", "SECURITY.md", "RELEASING.md"):
        assert set(pattern.findall(read(name))) <= {OPENSSF_PROJECT}, f"{name} names another badge entry"


def test_the_classifiers_list_every_supported_python():
    # the Pythons the package declares, the ones CI tests, and the ones PyPI is told about agree
    classified = set(re.findall(r'"Programming Language :: Python :: (3\.\d+)"', read("src/enbid_ananke/__metadata__.py")))
    bounds = re.search(r"python_requires\s*=\s*['\"]>=3\.(\d+),\s*<3\.(\d+)", read("setup.py"))
    supported = {f"3.{minor}" for minor in range(int(bounds.group(1)), int(bounds.group(2)))}
    ci = read(".github/workflows/ci.yml")
    tested = set(re.findall(r'"(3\.\d+)"', re.search(r"python-version:\s*\[([^\]]*)\]", ci).group(1)))
    assert classified == supported == tested, (sorted(classified), sorted(supported), sorted(tested))


def test_the_documents_state_the_supported_python_range():
    # the range in setup.py is the one the README and the contributing guide give
    bounds = re.search(r"python_requires\s*=\s*['\"]>=3\.(\d+),\s*<3\.(\d+)", read("setup.py"))
    first, last = bounds.group(1), int(bounds.group(2)) - 1
    assert f"Python 3.{first} to 3.{last}, on a Unix system" in read("README.md")
    contributing = read("CONTRIBUTING.md")
    assert f"each Python version from 3.{first} to 3.{last}, installs" in contributing
    assert f"(currently 3.{first} up to 3.{last})" in contributing


def test_python_sources_compile_without_warnings():
    # An invalid escape sequence ("\s" in a plain string) is only a warning today: a DeprecationWarning, then
    # a SyntaxWarning, and the one a future Python turns into an error. What versioneer generates is exempt.
    exempt = {"versioneer.py", "_version.py"}
    sources = (list((ROOT / "src").rglob("*.py")) + list((ROOT / ".github").rglob("*.py"))
               + [ROOT / "setup.py", ROOT / "docs" / "source" / "conf.py"])
    problems = []
    for path in sources:
        if path.is_symlink() or path.name in exempt or "Enbid-2.0" in path.parts or not path.is_file():
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except Exception as error:
                problems.append(f"{path.relative_to(ROOT)}: {error}")
    assert not problems, problems


def test_the_license_is_said_the_same_way_everywhere():
    assert json.loads(read(".zenodo.json"))["license"] == "GPL-2.0-or-later"
    assert re.search(r"^license: GPL-2.0-or-later$", read("CITATION.cff"), flags=re.MULTILINE)
    assert "(GPLv2+)" in read("src/enbid_ananke/__metadata__.py")


def test_zenodo_and_citation_files_name_the_same_software():
    title = json.loads(read(".zenodo.json"))["title"]
    assert re.search(rf'^title: "{re.escape(title)}"$', read("CITATION.cff"), flags=re.MULTILINE)


def test_source_files_carry_the_license_header():
    # empty files, Sphinx's conf.py, and what versioneer generates are the exceptions; so is
    # a symlink that a checkout without symlink support holds as a line of text
    exempt = {"conf.py", "_version.py", "versioneer.py"}
    missing = []
    candidates = list((ROOT / "src").rglob("*.py")) + list((ROOT / ".github").rglob("*.py")) + [ROOT / "setup.py"]
    for path in candidates:
        if path.is_symlink() or path.name in exempt or "Enbid-2.0" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.splitlines()) >= 3 and "(GPL-2.0-or-later)" not in text:
            missing.append(str(path.relative_to(ROOT)))
    assert not missing, f"no GPL-2.0-or-later header in: {missing}"


# -- the changelog -----------------------------------------------------------------

def test_changelog_format():
    text = read("CHANGELOG.md")
    headings = re.findall(r"^## \[([^\]]+)\](.*)$", text, flags=re.MULTILINE)
    names = [name for name, _ in headings]
    assert names and names[0] == "Unreleased", "the first section has to be [Unreleased]"
    for name, rest in headings[1:]:
        assert re.fullmatch(r" - \d{4}-\d{2}-\d{2}", rest), f"[{name}] needs '## [{name}] - YYYY-MM-DD'"
    links = set(re.findall(r"^\[([^\]]+)\]:\s", text, flags=re.MULTILINE))
    assert set(names) <= links, f"no link at the bottom for: {sorted(set(names) - links)}"


def test_changelog_tells_what_came_before_0_2_0():
    # the package did not start with 0.2.0, and the changelog must not read as if it did
    text = read("CHANGELOG.md")
    assert re.search(r"^## Before 0\.2\.0$", text, flags=re.MULTILINE)
    for tag in ("v0.0.0-alpha", "v0.1.3-beta", "v0.2.0b3"):
        assert tag in text
