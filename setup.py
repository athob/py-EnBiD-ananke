#!/usr/bin/env python
import setuptools
from setuptools import setup

from src._build_utils import *
from src._constants import NAME, SRC_DIR
from src.__metadata__ import *

with open("README.md") as readme:
    long_description = readme.read()

setup(name=NAME,
      version=__version__,
      author=__author__,
      author_email=__email__,
      maintainer=__maintainer__,
      maintainer_email=__email__,
      url=__url__,
      description=f"{__project__}: {__description__}",
      long_description=long_description,
      long_description_content_type="text/markdown",
      classifiers=__classifiers__,
      license=__license__,
      copyright=__copyright__,
      python_requires='>=3.8,<3.14',
      packages=setuptools.find_namespace_packages(
          SRC_DIR, exclude=['tests']),
      package_dir={'': SRC_DIR},
      package_data=make_package_data(),
      include_package_data=True,
      install_requires=['numpy>=1.22,<2', 'pandas>=2,<3', 'scikit-learn>=1.1,<2'],
    #   ext_modules=[setuptools.extension.Extension('', [])],
      cmdclass=make_cmdclass(),
      )
