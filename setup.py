#!/usr/bin/env python
import pathlib
import setuptools
from setuptools import setup

from src._build_utils import *
from src._constants import NAME, LOG_DIR, SRC_DIR, CONSTANTS
from src.__metadata__ import *

ROOT_DIR = pathlib.Path(__file__).parent

for_all_files = (CONSTANTS.enbid2, '__license__')

(ROOT_DIR / LOG_DIR).mkdir(parents=True, exist_ok=True)

long_description = ""

########## This can't be in MyBuildExt ##########
enbid_dir = ROOT_DIR / SRC_DIR / NAME / CONSTANTS.enbid2
download_enbid(enbid_dir)
compile_enbid(enbid_dir)
############## Because of that bit ##############
package_data = {NAME: all_files(*for_all_files,
                                basedir=pathlib.Path(SRC_DIR, NAME))}
#################################################

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
      python_requires='>=3.8,<3.12',
      packages=[NAME],
      package_dir={'': SRC_DIR},
      package_data=package_data,
      include_package_data=True,
      install_requires=['numpy>=1.22,<2', 'pandas>=2,<3', 'scikit-learn>=1.1,<2'],
      ext_modules=[setuptools.extension.Extension('', [])],
      cmdclass=make_cmdclass(),
      )
