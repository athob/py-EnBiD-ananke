# py-EnBiD-ananke

[![PyPI - Version](https://img.shields.io/pypi/v/enbid_ananke)](https://pypi.org/project/enbid-ananke/)
[![CI](https://github.com/athob/py-EnBiD-ananke/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/athob/py-EnBiD-ananke/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/py-enbid-ananke/badge/?version=latest)](https://py-enbid-ananke.readthedocs.io/en/latest/?badge=latest)
[![DOI](https://zenodo.org/badge/473607925.svg)](https://zenodo.org/badge/latestdoi/473607925)
[![License](https://img.shields.io/badge/license-GPL--2.0--or--later-blue.svg)](https://github.com/athob/py-EnBiD-ananke/blob/main/LICENSE)
[![Slack](https://img.shields.io/badge/slack-chat-green.svg)](https://join.slack.com/t/ananke-users/shared_invite/zt-37wmyn7ki-kmroxUul2W_VdFlEt0qCig)

Python wrapper for EnBiD ([Sharma & Steinmetz 2011](http://ascl.net/1109.012)), to be used by [py-ananke](https://github.com/athob/py-ananke).

## Installation

The package can be installed from PyPI:

```bash
pip install enbid_ananke
```

To use a version available on the repository instead, give the branch of your choice (here [main](https://github.com/athob/py-EnBiD-ananke/tree/main)):

```bash
pip install git+https://github.com/athob/py-EnBiD-ananke@main
```

A last option is to clone the repository, check out the branch of your choice and run `pip install .` from its root.

### Requirements

Python 3.8 to 3.14, on a Unix system: Windows is not supported. Whenever pip has to build the package (from the repository, or where no ready-made wheel is available), the build downloads the EnBiD source (from SourceForge) and compiles it, which needs network access, `tar`, GNU make (3.82 or later) and g++ (8.5 or later).

## Usage

Visit the [jupyter](https://github.com/athob/py-EnBiD-ananke/tree/main/jupyter) directory for example uses, and the [documentation](https://py-enbid-ananke.readthedocs.io) for the API reference.

## Citing

If you use py-EnBiD-ananke in your work, please cite, in this order:

1. The py-ananke article ([Thob et al. 2024](https://doi.org/10.21105/joss.06234)): this is the main citation. GitHub's "Cite this repository" button gives it in the usual formats, from [`CITATION.cff`](https://github.com/athob/py-EnBiD-ananke/blob/main/CITATION.cff).
2. The Zenodo record of py-EnBiD-ananke itself ([10.5281/zenodo.13937082](https://doi.org/10.5281/zenodo.13937082)). The article alone could suggest that the whole py-ananke pipeline was used; this one makes clear that py-EnBiD-ananke was the software. That DOI stands for all versions; each release also has a DOI of its own on Zenodo, which is the one to cite to name the version you used.
3. EnBiD ([Sharma & Steinmetz 2011](http://ascl.net/1109.012)), the code this package wraps.

## Contributing

Bug reports and feature requests go to the [issue tracker](https://github.com/athob/py-EnBiD-ananke/issues), which has a form for each. Contributions are welcome: see [CONTRIBUTING.md](https://github.com/athob/py-EnBiD-ananke/blob/main/CONTRIBUTING.md), and the [code of conduct](https://github.com/athob/py-EnBiD-ananke/blob/main/CODE_OF_CONDUCT.md). Please report security problems privately, as described in [SECURITY.md](https://github.com/athob/py-EnBiD-ananke/blob/main/SECURITY.md).

## License

py-EnBiD-ananke is licensed under the GNU General Public License v2.0 or later: see [LICENSE](https://github.com/athob/py-EnBiD-ananke/blob/main/LICENSE) and [COPYRIGHT](https://github.com/athob/py-EnBiD-ananke/blob/main/COPYRIGHT). EnBiD itself, which the package builds and ships, is distributed under the same terms.
