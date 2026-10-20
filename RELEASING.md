# Releasing

How a version of py-EnBiD-ananke gets released. It is a short checklist: the
[CD workflow](.github/workflows/cd.yml) does the publishing, and starts when a tag is
pushed.

## Which tag

A tag is `v` followed by a plain [PEP 440](https://peps.python.org/pep-0440/) version.
What happens depends on its kind:

| Tag                                   | Kind        | Published to                                     |
|---------------------------------------|-------------|--------------------------------------------------|
| `v0.3.4`, `v0.3.4.post1`              | release     | TestPyPI, then PyPI, then a GitHub release       |
| `v0.3.4a1`, `v0.3.4b1`, `v0.3.4rc0`   | pre-release | TestPyPI only, once CI has passed on the commit  |
| `v0.3.4.dev0`, `v0.3.4rc0.dev1`       | development | TestPyPI only, straight away                     |

Anything else (`v0.3.4-test`, `v0.3.4dev1`, ...) is refused by the first job of the
workflow, so that nothing that is not a clean release can reach PyPI. Development tags
are for trying the pipeline out. TestPyPI refuses a file name it has already seen, even
after deleting it, so every try needs a new number (`.dev1`, `.dev2`, ...).

## Trying the build

To try a change to the build (the image it runs in, the Python it builds with) without
publishing anything, run the CD workflow by hand: from the Actions tab, or with
`gh workflow run cd.yml --ref BRANCH`. It builds the sdist and the wheel, lists them in the
summary of the run (the platform tag of the wheel says which systems it installs on) and
keeps them as the `python-package-distributions` artifact; it publishes nothing, on any
branch or tag. GitHub only offers this for a workflow whose trigger is on the default
branch, so `main` has to have it first.

## The build image

The wheel is built in the `manylinux2014` image (`quay.io/pypa/manylinux2014_x86_64`), which
gives it the widest compatibility there is: the tags `manylinux2014` and `manylinux_2_17`, so
any Linux with glibc 2.17 or newer. PyPA's support for that image ends on **2027-05-04**:
until then it still gets updates, and after that it does not.

What the end of support does and does not mean:

- A wheel that is already on PyPI stays there, and pip keeps installing it on every system its
  tag allows, new systems included: a `manylinux2014` wheel is not tied to the image that built
  it, and old tags keep working on newer systems.
- Only the builds made after that date are affected: they would have to move to a newer image.

The cost of moving was measured in October 2026, with the manual build on a branch. The platform
tag comes from the glibc symbol versions the compiled executables need (`auditwheel show` prints
them in the log of the build), not from the name of the image:

| Image            | `libm.so.6` needs           | Tags of the wheel                  |
|------------------|-----------------------------|------------------------------------|
| `manylinux2014`  | `GLIBC_2.2.5`               | `manylinux2014`, `manylinux_2_17`  |
| `manylinux_2_28` | `GLIBC_2.2.5`, `GLIBC_2.27` | `manylinux_2_27`, `manylinux_2_28` |

So building in `manylinux_2_28` makes the wheel need glibc 2.27 instead of 2.17, because of the
version of some `libm` functions: everything else is equal. Systems with an older glibc (RHEL and
CentOS 7, Debian 9, Ubuntu 16.04) would install the sdist instead, and compile EnBiD themselves.

The plan is to keep building in `manylinux2014` while it is supported, and to move before
2027-05-04: change the image and the name of the step in `cd.yml`, after trying it with a manual
build on a branch (`gh workflow run cd.yml --ref BRANCH`) and reading the `auditwheel show` and
`New filename tags` lines of its log again, in case the answer has changed.

## Steps

1. Everything for the release is on `develop`, and the CI run of that commit is green
   (`stable` then points at it).
2. In [`CHANGELOG.md`](CHANGELOG.md), turn `## [Unreleased]` into
   `## [0.3.4] - YYYY-MM-DD`, add a new empty `## [Unreleased]` above it, and update the
   links at the bottom of the file (`[Unreleased]` compares the new tag with `develop`;
   `[0.3.4]` compares the previous tag with the new one). Commit it.
3. Optionally try the pipeline first with a pre-release, `v0.3.4rc0`: it goes to
   TestPyPI after CI, and the release itself then only differs by going to PyPI.
4. Tag the commit and push the tag:

   ```bash
   git tag v0.3.4
   git push origin v0.3.4
   ```

5. Move `main` to the released commit: `git switch main && git merge --ff-only v0.3.4
   && git push`.

The workflow then runs these jobs, and stops at the first one that fails:

1. **Classify the tag**: the tag has to be a version as above, and for a release
   `CHANGELOG.md` has to have its dated section. This is the reason to write the
   changelog first: nothing is built or published without it.
2. **Build**: for a pre-release, waits for the CI run of the tagged commit to succeed;
   then builds the sdist and the wheel inside a manylinux2014 container, and repairs the
   wheel with auditwheel.
3. **TestPyPI**, then, for a release only, **PyPI**.
4. **GitHub release**, for a release only: its notes are the changelog section, and
   the sdist and the wheel are attached. Zenodo archives the published release and
   gives that version its DOI.

Publishing uses PyPI's trusted publishing, through the `release` environment: no API
token is stored anywhere. The trusted publisher registered on both PyPI and TestPyPI
names the workflow file, `cd.yml`, and that environment.

## Afterwards

- Check the new version on [PyPI](https://pypi.org/project/enbid-ananke/), the
  [release](https://github.com/athob/py-EnBiD-ananke/releases) and its
  [Zenodo record](https://doi.org/10.5281/zenodo.13937082) (that DOI resolves to the
  latest version), and that the documentation built on Read the Docs.
- Update what depends on the new version (py-ananke, for one).

## If it goes wrong

- A tag refused by the first job, or a job that failed before anything was published:
  fix the cause, delete the tag (`git tag -d v0.3.4 && git push --delete origin v0.3.4`)
  and tag again.
- A job that failed after the files reached TestPyPI or PyPI: do not tag again, as those
  services never accept the same file twice. Use **Re-run failed jobs** on the run in the
  Actions tab, which only repeats what did not succeed. If the files themselves were
  wrong, release a new version instead (`v0.3.4.post1`, or the next one).
- A GitHub release created by hand before the workflow got there is completed by it (its
  notes and files are replaced), not refused.
