Installation instructions
=========================

Requirements
------------

Python 3.8 to 3.15, on a Unix system: Windows is not supported. Whenever pip has to build the package (from the repository, or where no ready-made wheel is available), the build downloads the EnBiD source (from SourceForge) and compiles it, which needs network access, ``tar``, GNU make (3.82 or later) and g++ (8.5 or later).

Dependencies
------------

``enbid_ananke`` requires the use of the following modules:

- numpy v1.22 and after, before v3
- pandas v2 and after, before v4
- scikit-learn v1.1 and after, before v2

Installation
------------

The package can be installed from PyPI::

    pip install enbid_ananke

To use a version available on the repository instead, give the branch of your choice (here ``main``)::

    pip install git+https://github.com/athob/py-EnBiD-ananke@main

A last option is to clone the repository, check out the branch of your choice and run ``pip install .`` from its root.
