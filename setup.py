#!/usr/bin/env python
import pathlib
import distutils
from distutils.command.build_ext import build_ext
from distutils.cmd import Command
from distutils.core import setup

from src._build_utils import *
from src.constants import NAME, LOG_DIR, SRC_DIR, CONSTANTS
from src.__metadata__ import *

ROOT_DIR = pathlib.Path(__file__).parent

for_all_files = (CONSTANTS.enbid2,)

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


# Custom build step that manually creates the makefile and then calls 'make' to create the shared library
class MyBuildExt(build_ext):
    def run(self):
        # try:
        #     say("\nTesting if Enbid is available...")
        #     enbid_exists = bool(subprocess.call('Enbid'))
        #     say("Done\n")
        # except (PermissionError, OSError):
        #     say("Absent\n")
        #     enbid_exists = False
        enbid_exists = False  # TODO
        if not enbid_exists:
            ########## This can't be in MyBuildExt ##########
            # enbid_dir = ROOT_DIR / SRC_DIR / NAME / CONSTANTS.enbid2
            # download_enbid(enbid_dir)
            # compile_enbid(enbid_dir)
            #################################################
            pass


class MyTest(Command):
    description = 'run tests'
    user_options = []

    def initialize_options(self): pass

    def finalize_options(self): pass

    def run(self): pass


setup(name=NAME,
      version=__version__,
      author=__author__,
      author_email=__email__,
      maintainer=__maintainer__,
      maintainer_email=__email__,
      url="https://github.com/athob/py-EnBiD-ananke",
      description="",
      long_description=long_description,
      long_description_content_type="text/markdown",
      classifiers=[
          __status__,
          "Environment :: Console",
          "Intended Audience :: Science/Research",
          __license__,
          "Natural Language :: English",
          "Operating System :: Unix",
          "Programming Language :: Python :: 3",
          "Topic :: Database",
          "Topic :: Scientific/Engineering :: Astronomy",
          "Topic :: Software Development :: Version Control :: Git"
      ],
      python_requires='>=3.7.12,<3.12',
      packages=[NAME],
      package_dir={'': SRC_DIR},
      package_data=package_data,
      include_package_data=True,
      install_requires=['numpy>=1.22,<2', 'pandas>=2,<3', 'scikit-learn>=1.1,<2'],
      ext_modules=[distutils.extension.Extension('', [])],
      cmdclass={'build_ext': MyBuildExt, 'test': MyTest},
      )
