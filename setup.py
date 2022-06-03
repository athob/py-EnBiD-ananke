#!/usr/bin/env python
"""
Credit to https://github.com/GalacticDynamics-Oxford/Agama/blob/master/setup.py for tools
"""
import os
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

ROOT_DIR = os.path.split(os.path.abspath(__file__))[0]
NAME = 'EnBiD'
LOG_DIR = 'log'
SRC_DIR = 'src'

ENBID2 = eval(subprocess.check_output(["grep", "ENBID2 =",
                                       os.path.join(ROOT_DIR, SRC_DIR, NAME, "constants.py")]).decode().split('=')[-1])
for_all_files = (ENBID2,)

try:
    os.mkdir(os.path.join(ROOT_DIR, LOG_DIR))
except FileExistsError:
    pass

long_description = ""

# metadata are set in the below file, but use this here to avoid warnings.
__author__ = __copyright__ = __credits__ = __license__ = __version__ = __maintainer__ = __email__ = __status__ = None
exec(open(os.path.join(ROOT_DIR, SRC_DIR, NAME, "__metadata__.py")).read())


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
    basedir = os.path.normpath(basedir) + os.sep
    return [os.path.join(dirpath, f)[len(basedir):]
            for path in paths
            for dirpath, dirnames, files in os.walk(basedir + path)
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
            enbid_dir = os.path.join(SRC_DIR, NAME, ENBID2)
            tarfile = os.path.join(ROOT_DIR, enbid_dir + '.tar.gz')
            try:
                urllib.request.urlretrieve('https://sourceforge.net/projects/enbid/files/latest/download',
                                           filename=tarfile)
                if os.path.isfile(tarfile):
                    say("\nUnpacking Enbid")
                    subprocess.call(['tar', 'xzvf', tarfile, '-C', os.path.split(tarfile)[0]])
                    os.remove(tarfile)
                    if not os.path.isdir(enbid_dir):
                        raise RuntimeError("Error unpacking Enbid")
                else:
                    raise RuntimeError("Cannot find downloaded file")
            except RuntimeError as e:
                raise CompileError(str(e) + "\nError downloading Enbid, aborting...\n")
            say("\nCompiling Enbid")
            # CONFIGURING MAKEFILE #
            makefile = os.path.join(ROOT_DIR, enbid_dir, 'src', 'Makefile')
            for line in fileinput.input(makefile, inplace=True):
                if bool(re.match(r".*OPT2.*=", line)):
                    line = re.sub(r'.*OPT2',  '{}OPT2'.format('' if re.match(r".*-DDIM3", line) else '#'), line)
                print(line, end='')
            # END CONFIGURATION #
            result = subprocess.call('(cd ' + os.path.join(ROOT_DIR, enbid_dir, 'src') + '; make) > ' +
                                     os.path.join('.', LOG_DIR, 'Enbid-make.log'),
                                     shell=True)
            if result != 0 or not os.path.isfile(os.path.join(enbid_dir, 'Enbid')):
                raise CompileError("Enbid compilation failed (check " +
                                   os.path.join(".", LOG_DIR, "Enbid-make.log") + ")")
            os.chdir(ROOT_DIR)


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
      package_data={NAME: all_files(*for_all_files, basedir=os.path.join(SRC_DIR, NAME))},
      include_package_data=True,
      install_requires=['numpy', 'pandas'],
      ext_modules=[distutils.extension.Extension('', [])],
      cmdclass={'build_ext': MyBuildExt, 'test': MyTest},
      )
