#!/usr/bin/env python
"""
Credit to https://github.com/GalacticDynamics-Oxford/Agama/blob/master/setup.py for tools
"""
import pathlib
import sys
import re
import fileinput
import subprocess
import urllib.request
import distutils
from distutils.errors import CompileError
from distutils.command.build_ext import build_ext as CmdBuildExt
from distutils.cmd import Command
from distutils.core import setup

ROOT_DIR = pathlib.Path(__file__).parent
NAME = 'EnBiD'
LOG_DIR = 'log'
SRC_DIR = 'src'

ENBID2 = eval(subprocess.check_output(["grep", "ENBID2 =",
                                       ROOT_DIR / SRC_DIR / NAME / "constants.py"]).decode().split('=')[-1])
ENBID_URL = eval(subprocess.check_output(["grep", "ENBID_URL =",
                                          ROOT_DIR / SRC_DIR / NAME / "constants.py"]).decode().split('=')[-1])
for_all_files = (ENBID2,)

(ROOT_DIR / LOG_DIR).mkdir(parents=True, exist_ok=True)

long_description = ""

# metadata are set in the below file, but use this here to avoid warnings.
__author__ = __copyright__ = __credits__ = __license__ = __version__ = __maintainer__ = __email__ = __status__ = None
exec(open(ROOT_DIR / SRC_DIR / NAME / "__metadata__.py").read())


# force printing to the terminal even if stdout was redirected
def say(text):
    text += ' '
    sys.stdout.write(text)
    sys.stdout.flush()
    if not sys.stdout.isatty():
        # output was redirected, but we still try to send the message to the terminal
        try:
            with open('/dev/tty', 'w') as out:
                out.write(text)
                out.flush()
        except PermissionError:
            # /dev/tty may not exist or may not be writable!
            pass


# get the list of all files in the given directories (including those in nested directories)
def all_files(*paths, basedir='.'):
    basedir = pathlib.Path(basedir)
    return [str(pathlib.Path(dirpath, f).relative_to(basedir))
            for path in paths
            for dirpath, dirnames, files in pathlib.os.walk(basedir / path)
            for f in files]


# Custom build step that manually creates the makefile and then calls 'make' to create the shared library
class MyBuildExt(CmdBuildExt):
    def run(self):
        try:
            say("\nTesting if Enbid is available...")
            enbid_exists = bool(subprocess.call('Enbid'))
            say("Done\n")
        except (PermissionError, OSError):
            say("Absent\n")
            enbid_exists = False
        enbid_exists = False  # TODO
        if not enbid_exists:
            say("\nDownloading Enbid")
            enbid_dir = pathlib.Path(SRC_DIR, NAME, ENBID2)
            tarfile = ROOT_DIR / enbid_dir.with_suffix('.tar.gz')
            try:
                urllib.request.urlretrieve(ENBID_URL, filename=tarfile)
                if tarfile.is_file():
                    say("\nUnpacking Enbid")
                    subprocess.call(['tar', 'xzvf', tarfile, '-C', tarfile.parent])
                    tarfile.unlink()
                    if not enbid_dir.is_dir():
                        raise RuntimeError("Error unpacking Enbid")
                else:
                    raise RuntimeError("Cannot find downloaded file")
            except RuntimeError as e:
                raise CompileError(str(e) + "\nError downloading Enbid, aborting...\n")
            say("\nCompiling Enbid")
            # CONFIGURING MAKEFILE #
            makefile = ROOT_DIR / enbid_dir / 'src' / 'Makefile'
            for line in fileinput.input(makefile, inplace=True):
                if bool(re.match(r".*OPT2.*=", line)):
                    line = re.sub(r'.*OPT2',  '{}OPT2'.format('' if re.match(r".*-DDIM3", line) else '#'), line)
                print(line, end='')
            # END CONFIGURATION #
            with pathlib.Path('.', LOG_DIR, 'Enbid-make.log').open('w') as f:
                result = subprocess.call(f"make", cwd=ROOT_DIR / enbid_dir / 'src', stdout=f, stderr=f)
            if result != 0 or not (enbid_dir / 'Enbid').is_file():
                raise CompileError(f"Enbid compilation failed (check {pathlib.Path('.', LOG_DIR, 'Enbid-make.log')})")


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
      url="https://github.com/athob/py-EnBiD",
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
      python_requires='>=3',
      packages=[NAME],
      package_dir={'': SRC_DIR},
      package_data={NAME: all_files(*for_all_files, basedir=pathlib.Path(SRC_DIR, NAME))},
      include_package_data=True,
      install_requires=['numpy', 'pandas'],
      ext_modules=[distutils.extension.Extension('', [])],
      cmdclass={'build_ext': MyBuildExt, 'test': MyTest},
      )
