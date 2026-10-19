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
