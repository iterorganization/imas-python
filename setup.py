#! /usr/bin/env python
"""
Packaging settings. Inspired by a minimal setup.py file, the Pandas cython build and the access-layer setup template
"""
import os
import shutil
import argparse
import sys
from itertools import chain
from codecs import open
from subprocess import call

from distutils.version import LooseVersion
from distutils import sysconfig
from setuptools import Command, find_packages, setup

import numpy #WHY?
from distutils.command.build import build as _build


this_dir = os.path.abspath(os.path.dirname(__file__)) # We need to know where we are for many things
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
    for ext in extensions:
        if ext.name.startswith('ual_'):
            version = ext.name[4:].split('.')[0]
            if version != '0.0.0':
                sources_prepared = prepare_ual_sources(force=fail_on_ual_fail)
                if not sources_prepared:
                    print('Not cythonizing', ext.name)
                    extensions.remove(ext)

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

def prepare_ual_sources(force=False):
    import git # Import git here, the user might not have it!

    # This will probably _always_ depend on the UAL version.
    # However, opposed to the original Python HLI, it does not
    # depend on the IMAS DD version, as that is build dynamically in runtime

    # Now we know which UAL target the user wants to install
    # We need the actual source code (for now) so grab it from ITER
    ual_repo_path = 'src/ual'
    ual_repo_url = 'ssh://git@git.iter.org/imas/access-layer.git'

    # Set up a bare repo and fetch the access-layer repository in it
    os.makedirs(ual_repo_path, exist_ok=True)
    try:
        repo = git.Repo(ual_repo_path)
    except git.exc.InvalidGitRepositoryError:
        repo = git.Repo.init(ual_repo_path)
    print("Set up local git repository {!s}".format(repo))

    try:
        origin = repo.remote()
    except ValueError:
        origin = repo.create_remote('origin', url=ual_repo_url)

    print("Set up remote '{!s}' linking to '{!s}'".format(origin, origin.url))
    refspec=':' + ual_commit
    print('Fetching refspec {!s}'.format(refspec))

    try:
        fetch_results = origin.fetch(refspec=refspec)
    except git.exc.GitCommandError:
        msg = 'Could not find ual_commit {!s}'.format(ual_commit)
        if force:
            raise ValueError(msg)
        else:
            print(msg)
            return
    if len(fetch_results) == 0:
        # We already had the commit, find the head of it
        head = None
        for head in repo.heads:
            if head.name == ual_commit:
                head = head
    else:
        # We fetched the commit, use as HEAD
        fetch_result = fetch_results[-1]
        head = repo.create_head(ual_commit, commit=fetch_result)

    # Check out remote files locally
    head.checkout()
    described_version = repo.git.describe()
    if UAL_VERSION_SAFE.replace('_', '.') != described_version:
        raise Exception("Fetched head commit '{!s}' with description '{!s}' does not match UAL_VERSION '{!s}'".format(head.commit, described_version, UAL_VERSION))


    # We should now have the Python HLI files, check
    hli_src = os.path.join(this_dir, ual_repo_path, 'pythoninterface/src/imas')
    if not os.path.isdir(hli_src):
        raise Exception('Python interface src dir does not exist. Should have failed earlier')


    # For the build, we need these
    ual_cython_filelist = ['_ual_lowlevel.pyx', 'ual_defs.pxd', 'ual_lowlevel_interface.pxd']
    # We need these in runtime, so check them here
    filelist = ['imasdef.py', 'hli_utils.py', 'hli_exception.py']

    # Copy these files into the imaspy directory
    # TODO: This is a bit hacky, do this nicer
    imaspy_libs_dir = os.path.join(this_dir, 'imaspy/_libs')
    os.makedirs(imaspy_libs_dir, exist_ok=True)
    #if len(os.listdir(imaspy_libs_dir)) != 0:
        #raise Exception('imaspy libs dir not empty, refusing to overwrite')
    # Make _libs dir act as a python module
    open(os.path.join(imaspy_libs_dir, '__init__.py'), 'w').close()

    for file in chain(ual_cython_filelist, filelist):
        path = os.path.join(hli_src, file)
        if not os.path.isfile(path):
            raise Exception('Could not find {!s}, should have failed earlier'.format(path))
        else:
            target_path = os.path.join(imaspy_libs_dir, file)
            # Patch some imports, they are different from regular Python HLI and imaspy
            # From PEP-8, absolute imports are preferred https://www.python.org/dev/peps/pep-0008/#id23
            if file == '_ual_lowlevel.pyx':
                with open(path, 'r') as old, open(target_path, 'w') as new:
                    for line in old:
                        if line == 'cimport ual_lowlevel_interface as ual\n':
                            new.write('cimport imaspy._libs.ual_lowlevel_interface as ual\n')
                        elif line == 'from imasdef import *\n':
                            new.write('from imaspy._libs.imasdef import *\n')
                        elif line == 'from hli_exception import ALException \n':
                            new.write('from imaspy._libs.hli_exception import ALException\n')
                        else:
                            new.write(line)
            else:
                shutil.copyfile(path, os.path.join(imaspy_libs_dir, file))

    return True

with open(os.path.join(this_dir, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

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

# Try to grab all necessary environment variables.
# IMAS_PREFIX points to the directory all IMAS components live in
IMAS_PREFIX = os.getenv("IMAS_PREFIX")
if not IMAS_PREFIX or not os.path.isdir(IMAS_PREFIX):
    print('IMAS_PREFIX is unset or is not a directory. Points to {!s}. Will not build UAL!'.format(IMAS_PREFIX))
    IMAS_PREFIX = '0.0.0'

# Legacy code, we do not need an explicit IMAS_VERSION.
# What is more important, we need the UAL_VERSION we want to link
# to
## Sanity checks, fallback to 0.0.0_0.0.0
#IMAS_VERSION = os.getenv("IMAS_VERSION")
#if not IMAS_VERSION or not len(IMAS_VERSION.split("."))>2:
#    print('IMAS_VERSION is unset or is not formatted as "0.0.0"')
#    IMAS_VERSION = "0.0.0"
#MAJOR = IMAS_VERSION.split(".")[0]
#MINOR = IMAS_VERSION.split(".")[1]

# Grab the UAL_VERSION to build against
UAL_VERSION = os.getenv("UAL_VERSION")
if not UAL_VERSION:
    print('UAL_VERSION is unset. Will not build UAL!')
    UAL_VERSION = '0.0.0'

# Safeify the UAL_VERSION
if '-' in UAL_VERSION:
    ual_patch_version, micropatch = UAL_VERSION.split('-', 1)
    steps_from_version, commitspec = micropatch.split('-', 2)
    ual_commit = commitspec[1:]
else:
    ual_patch_version = UAL_VERSION
    ual_commit = UAL_VERSION
UAL_VERSION_SAFE = ual_patch_version.replace('.', '_')

# We need source files of the Python HLI UAL library
# to link our build against, the version is grabbed from
# the environment, and they are saved as syubdirectory of
# imaspy
pxd_path = os.path.join(this_dir, 'imaspy/_libs')

ext_module_name = "ual_{!s}._ual_lowlevel".format(UAL_VERSION_SAFE)

LANGUAGE = 'c' # Not sure when this is not true
LIBRARIES = 'imas' # We just need the IMAS library
#EXTRALINKARGS = '' # This is machine-specific ignore for now
#EXTRACOMPILEARGS = '' # This is machine-specific ignore for now

ext_module = Extension(
  name = ext_module_name,
  sources = [ "imaspy/_libs/_ual_lowlevel.pyx" ], # As these files are copied, easy to find!
  language = LANGUAGE,
  library_dirs = [ IMAS_PREFIX + "/lib" ],
  libraries = [ LIBRARIES ],
  #extra_link_args = [ EXTRALINKARGS ],
  #extra_compile_args = [ EXTRACOMPILEARGS ],
  include_dirs=[ IMAS_PREFIX + "/include", numpy.get_include(), pxd_path],
)
ext_modules = []

parser = argparse.ArgumentParser()
parser.add_argument("--build-ual", action='store_true')
args, leftovers = parser.parse_known_args()
fail_on_ual_fail = args.build_ual

if ext_module is not None:
    ext_modules.append(ext_module)
else:
    print('Cannot build UAL')

setup(
    name = 'imaspy',
    version = '0.0.1',
    description = '.',
    long_description = long_description,
    url = 'https://gitlab.com/Karel-van-de-Plassche/imaspy',
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
    ext_modules = maybe_cythonize(ext_modules),
    cmdclass = {'test': RunTests, "build_ext": build_ext, "build": _build },
)
