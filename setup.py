#! /usr/bin/env python
"""
Packaging settings. Inspired by a minimal setup.py file, the Pandas cython build and the access-layer setup template
"""
import os
import argparse
import sys
from codecs import open
from subprocess import call
from distutils.version import LooseVersion
from distutils import sysconfig
from setuptools import Command, find_packages, setup

import numpy #WHY?
from distutils.command.build import build as _build


### CYTHON COMPILATION MANGELING

min_cython_ver = "0.29.16" #No idea, guess something

try:
    import Cython

    _CYTHON_VERSION = Cython.__version__
    from Cython.Build import cythonize

    _CYTHON_INSTALLED = _CYTHON_VERSION >= LooseVersion(min_cython_ver)
except ImportError:
    raise
    _CYTHON_VERSION = None
    _CYTHON_INSTALLED = False
    cythonize = lambda x, *args, **kwargs: x  # dummy func

# The import of Extension must be after the import of Cython, otherwise
# we do not get the appropriately patched class.
# See https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html # noqa
from distutils.extension import Extension
from distutils.command.build import build

if _CYTHON_INSTALLED:
    #from Cython.Distutils.old_build_ext import old_build_ext as _build_ext # Do not use the old build_ext
    from Cython.Distutils import build_ext as _build_ext

    cython = True
    from Cython import Tempita as tempita
else:
    from distutils.command.build_ext import build_ext as _build_ext

    cython = False
build_ext = _build_ext # No monkey patching needed

def maybe_cythonize(extensions, *args, **kwargs):
    """
    Render tempita templates before calling cythonize. This is skipped for
    * clean
    * sdist
    """
    if "clean" in sys.argv or "sdist" in sys.argv:
        # See https://github.com/cython/cython/issues/1495
        return extensions

    elif not cython:
        # GH#28836 raise a helfpul error message
        if _CYTHON_VERSION:
            raise RuntimeError(
                f"Cannot cythonize with old Cython version ({_CYTHON_VERSION} "
                f"installed, needs {min_cython_ver})"
            )
        raise RuntimeError("Cannot cythonize without Cython installed.")

    # reuse any parallel arguments provided for compilation to cythonize
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", type=int)
    parser.add_argument("--parallel", type=int)
    parsed, _ = parser.parse_known_args()

    nthreads = 0
    if parsed.parallel:
        nthreads = parsed.parallel
    elif parsed.j:
        nthreads = parsed.j

    kwargs["nthreads"] = nthreads
    #build_ext.render_templates(_pxifiles)
    return cythonize(extensions, *args, **kwargs)

### IMAS-style package names
def get_ext_filename_without_platform_suffix(filename):
  """ Remove specific system filename extension """
  name, ext = os.path.splitext(filename)
  ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")

  if ext_suffix == ext:
    return filename

  ext_suffix = ext_suffix.replace(ext, "")
  idx = name.find(ext_suffix)

  if idx == -1:
    return filename
  else:
    return name[:idx] + ext

class BuildExtWithoutPlatformSuffix(build_ext):
  def get_ext_filename(self, ext_name):
    filename = super().get_ext_filename(ext_name)
    filename = get_ext_filename_without_platform_suffix(filename)
    # For Windows MINGW, replace extension ".dll" by ".pyd"
    filename = filename.replace(".dll", ".pyd")
    return filename

### External variables with fallbacks
config = {
    'IMASPKGNAME'        : None,
    'IMAS_VERSION_SAFE'  : None,
    'UAL_VERSION_SAFE'   : None,
    'IMAS_VERSION_SHORT' : None,
    'UAL_VERSION_SHORT'  : None,
    'IMASPKGVERSION'     : None,
    'EXTRALINKARGS'      : None,
    'EXTRACOMPILEARGS'   : None,
    'LIBRARIES'          : None,
    'OUTPUT_LIBRARY'     : None,
    'LANGUAGE'           : None,
}


IMAS_PREFIX = os.getenv("IMAS_PREFIX")
if not IMAS_PREFIX or not os.path.isdir(IMAS_PREFIX):
    # Why is this a problem?
    raise ValueError('IMAS_PREFIX is unset or is not a directory.')

# Sanity checks, fallback to 0.0.0_0.0.0
IMAS_VERSION = os.getenv("IMAS_VERSION")
if not IMAS_VERSION or not len(IMAS_VERSION.split("."))>2:
    print('IMAS_VERSION is unset or is not formatted as "0.0.0"')
    IMAS_VERSION = "0.0.0"
MAJOR = IMAS_VERSION.split(".")[0]
MINOR = IMAS_VERSION.split(".")[1]

# Grab info from the command line
parser = argparse.ArgumentParser()
parser.add_argument("-j", type=int)
parser.add_argument("--parallel", type=int)
parsed, _ = parser.parse_known_args()

if '-' in IMAS_VERSION:
    raise NotImplementedError
else:
    IMAS_VERSION_SAFE = IMAS_VERSION

UAL_VERSION = '4.7.2' # TODO: Do not hard code!
if '-' in UAL_VERSION:
    raise NotImplementedError
else:
    UAL_VERSION_SAFE = UAL_VERSION
# Example
# "s|@@IMASPKGNAME@@|imas_3_28_1_ual_4_7_2_dev38|g" \
# "s|@@IMAS_VERSION_SAFE@@|3.28.1|g" \
# "s|@@UAL_VERSION_SAFE@@|4.7.2|g" \
# "s|@@IMAS_VERSION_SHORT@@|3.28.1|g" \
# "s|@@UAL_VERSION_SHORT@@|4.7.2|g" \
# "s|@@IMASPKGVERSION@@|4.7.2.dev38+g2cc2ab8cdirty|g" \
# 's|@@EXTRALINKARGS@@||g' \
# 's|@@EXTRACOMPILEARGS@@|"-D__USE_XOPEN2K8"|g' \
# 's|@@LIBRARIES@@|"imas"|g' \
# 's|@@OUTPUT_LIBRARY@@||g' \
# 's|@@LANGUAGE@@|"c"|g' \

this_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_dir, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

LANGUAGE = 'c' # Not sure when this is not true
LIBRARIES = 'imas' # We just need the IMAS library
#EXTRALINKARGS = '' # This is machine-specific
#EXTRACOMPILEARGS = '' # This is machine-specific

# This will probably _always_depend on the UAL version. However, opposed to the original Python HLI, it does not depend on the IMAS DD version, as that is build dynamically in runtime
pxd_path = os.path.join(this_dir, 'pymas/_libs')
print(os.listdir(pxd_path))
ext_module_name = "ual_{!s}._ual_lowlevel".format(UAL_VERSION_SAFE.replace('.', '_'))
ext_module = Extension(
  name = ext_module_name,
  sources = [ "pymas/_libs/_ual_lowlevel.pyx" ], # As we're targetting a single UAL (For not), the sources are easy to find!
  language = LANGUAGE,
  library_dirs = [ IMAS_PREFIX + "/lib" ],
  libraries = [ LIBRARIES ],
  #extra_link_args = [ EXTRALINKARGS ],
  #extra_compile_args = [ EXTRACOMPILEARGS ],
  include_dirs=[ IMAS_PREFIX + "/include", numpy.get_include(), pxd_path],
)


class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test'])
        raise SystemExit(errno)

setup(
    name = 'pymas',
    version = '0.0.1',
    description = '.',
    long_description = long_description,
    url = 'https://gitlab.com/Karel-van-de-Plassche/pymas',
    author = 'Karel van de Plassche',
    author_email = 'karelvandeplassche@gmail.com',
    license = 'MIT',
    classifiers = [
        'Intended Audience :: Science/Research',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3'
    ],
    packages = find_packages(exclude=['docs', 'tests*']),
    install_requires = requirements,
    setup_requires = [ "numpy", "cython" ],
    extras_require = {
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    ext_modules = maybe_cythonize([ext_module]),
    cmdclass = {'test': RunTests, "build_ext": build_ext, "build": _build },
)
