"""
Packaging settings. Inspired by a minimal setup.py file, the Pandas cython build
and the access-layer setup template.

The reference method of installing is determined by the
[Python Package Authority](https://packaging.python.org/tutorials/installing-packages/)
of which a summary and advanced explanation is on the [IMASPy wiki](https://gitlab.com/imaspy-dev/imaspy/-/wikis/installing)

The installable IMASPy package tries to follow in the following order:
- The style guide for Python code [PEP8](https://www.python.org/dev/peps/pep-0008/)
- The PyPA guide on packaging projects https://packaging.python.org/guides/distributing-packages-using-setuptools/#distributing-packages
- The PyPA tool recommendations https://packaging.python.org/guides/tool-recommendations/, specifically:
  * Installing: [pip](https://pip.pypa.io/en/stable/)
  * Environment management: [venv](https://docs.python.org/3/library/venv.html)
  * Dependency managamenet: [pip-tools](https://github.com/jazzband/pip-tools)
  * Packaging source distributions: [setuptools](https://setuptools.readthedocs.io/)
  * Packaging built distribitions: [wheels](https://pythonwheels.com/)
"""
# Set up 'fancy logging' to display messages to the user
import logging
import imaspy
imaspy_logger = logging.getLogger('imaspy')
logger = imaspy_logger
logger.setLevel(logging.INFO)

logger.info("pyproject.toml support got added in pip 10. Assuming it is available")

###
# HANDLE USER ENVIRONMENT
###
import argparse
import os
from imaspy.imas_ual_env_parsing import parse_UAL_version_string, sanitise_UAL_patch_version, build_UAL_package_name
this_dir = os.path.abspath(os.path.dirname(__file__)) # We need to know where we are for many things
parser = argparse.ArgumentParser()
parser.add_argument("--build-ual", action='store_true')
args, leftovers = parser.parse_known_args()
fail_on_ual_fail = args.build_ual

# Now that the environment is defined, import the rest of the needed packages
import sys
import shutil
from itertools import chain
from subprocess import call
import logging
from distutils.version import LooseVersion
from distutils import sysconfig
from setuptools import Command, find_packages, setup, Extension



# Try to grab all necessary environment variables.
# IMAS_PREFIX points to the directory all IMAS components live in
IMAS_PREFIX = os.getenv("IMAS_PREFIX")
if not IMAS_PREFIX or not os.path.isdir(IMAS_PREFIX):
    logger.warning('IMAS_PREFIX is unset or is not a directory. Points to {!s}. Will not build UAL!'.format(IMAS_PREFIX))
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
    logger.warning('UAL_VERSION is unset. Will not build UAL!')
    UAL_VERSION = '0.0.0'

ual_patch_version, steps_from_version, ual_commit = parse_UAL_version_string(UAL_VERSION)

safe_ual_patch_version = sanitise_UAL_patch_version(ual_patch_version)
ext_module_name = build_UAL_package_name(safe_ual_patch_version, ual_commit)

# We need source files of the Python HLI UAL library
# to link our build against, the version is grabbed from
# the environment, and they are saved as syubdirectory of
# imaspy
pxd_path = os.path.join(this_dir, 'imaspy/_libs')

LANGUAGE = 'c' # Not sure when this is not true
LIBRARIES = 'imas' # We just need the IMAS library
#EXTRALINKARGS = '' # This is machine-specific ignore for now
#EXTRACOMPILEARGS = '' # This is machine-specific ignore for now

###
# Set up Cython build integration
###
### CYTHON COMPILATION ENVIRONMENT

# From https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html#multiple-cython-files-in-a-package
USE_CYTHON = True
cython_like_ext = '.pyx' if USE_CYTHON else '.c'

###
# Build extention list
###
extensions = []

import numpy as np
ual_module = Extension(
  name = ext_module_name,
  sources = [ "imaspy/_libs/_ual_lowlevel.pyx" ], # As these files are copied, easy to find!
  language = LANGUAGE,
  library_dirs = [ IMAS_PREFIX + "/lib" ],
  libraries = [ LIBRARIES ],
  #extra_link_args = [ EXTRALINKARGS ],
  #extra_compile_args = [ EXTRACOMPILEARGS ],
  include_dirs=[ IMAS_PREFIX + "/include", np.get_include(), pxd_path],
)
extensions.append(ual_module)

###
# Set up Cython compilation (or not)
###
def no_cythonize(extensions, **_ignore):
    for extension in extensions:
        sources = []
        for sfile in extension.sources:
            path, ext = os.path.splitext(sfile)
            if ext in ('.pyx', '.py'):
                if extension.language == 'c++':
                    ext = '.cpp'
                else:
                    ext = '.c'
                sfile = path + ext
            sources.append(sfile)
        extension.sources[:] = sources
    return extensions

extensions = no_cythonize(extensions)


### IMAS-style package names (Not use right now)
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

def prepare_ual_sources(force=False):
    """ Use gitpython to grab AL sources from ITER repository """
    try:
        import git # Import git here, the user might not have it!
    except ModuleNotFoundError:
        logger.warning("Could not find 'git' module, try 'pip install gitpython'. Will not build AL!")
        return False

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
    logger.info("Set up local git repository {!s}".format(repo))

    try:
        origin = repo.remote()
    except ValueError:
        origin = repo.create_remote('origin', url=ual_repo_url)
    logger.info("Set up remote '{!s}' linking to '{!s}'".format(origin, origin.url))

    origin.fetch('--tags')
    logger.info("Remote tags fetched")

    # First check if we have the commit already
    head = None
    for head in repo.heads:
        if head.name == ual_commit:
            head = head

    if head is None:
        logger.info("Commit '{!s}' not found locally, trying remote".format(ual_commit))
        # If we do not have the commit, fetch master
        #refspec='remotes/origin/' + ual_commit + ':' + ual_commit
        #refspec = ual_commit + ':' + ual_commit
        refspec = 'master'
        logger.info('Fetching refspec {!s}'.format(refspec))

        fetch_results = origin.fetch(refspec=refspec)
        if len(fetch_results) == 1:
            head = repo.create_head('HEAD', ual_commit)
        else:
            raise Exception("Could not create head HEAD from commit '{!s}'".format(ual_commit))

    # Check out remote files locally
    head.checkout()
    described_version = repo.git.describe()
    if safe_ual_patch_version.replace('_', '.') != described_version:
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
    extras_require = {
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    ext_modules = extensions,
    cmdclass = {'test': RunTests},
                #, "build_ext": build_ext},
)
