# pylint: disable=wrong-import-position
"""
Packaging settings. Inspired by a minimal setup.py file, the Pandas cython build
and the access-layer setup template.

The reference method of installing is determined by the
[Python Package Authority](https://packaging.python.org/tutorials/installing-packages/)
of which a summary and advanced explanation is on the [IMASPy wiki](https://gitlab.com/imaspy-dev/imaspy/-/wikis/installing)

The installable IMASPy package tries to follow in the following order:
- The style guide for Python code [PEP8](https://www.python.org/dev/peps/pep-0008/)
- The [PyPA guide on packaging projects](https://packaging.python.org/guides/distributing-packages-using-setuptools/#distributing-packages)
- The [PyPA tool recommendations](https://packaging.python.org/guides/tool-recommendations/), specifically:
  * Installing: [pip](https://pip.pypa.io/en/stable/)
  * Environment management: [venv](https://docs.python.org/3/library/venv.html)
  * Dependency management: [pip-tools](https://github.com/jazzband/pip-tools)
  * Packaging source distributions: [setuptools](https://setuptools.readthedocs.io/)
  * Packaging built distributions: [wheels](https://pythonwheels.com/)

On the ITER cluster we handle the environment by using the `IMAS` module load.
So instead, we install packages to the `USER_SITE` there, and do not use
`pip`s `build-isolation`. See [IMAS-584](https://jira.iter.org/browse/IMAS-584)
"""
# Allow importing local files, see https://snarky.ca/what-the-heck-is-pyproject-toml/
import sys

if sys.version_info < (3, 6):
    sys.exit(
        "Sorry, Python < 3.6 is not supported. Use a different"
        " python e.g. 'module swap python Python/3.6.4-foss-2018a'"
    )

# Use setuptools to build packages
from setuptools import setup, find_packages, __version__ as setuptools_version

from distutils.version import LooseVersion as V

import os
import argparse
from pathlib import Path
import logging
from IPython import embed  # pylint: disable=unused-import # noqa: F401 For debugging
# Check setuptools version before continuing for legacy builds
if V(setuptools_version) < V('42'):
    raise Exception(f'Setuptools version outdated. Found {setuptools_version}')


import distutils.sysconfig
import distutils.util

platform = distutils.util.get_platform()  # linux-x86_64
distutils.util.check_environ()
import distutils.text_file

plat_indep_libraries = Path(distutils.sysconfig.get_python_lib())
plat_indep_include = Path(distutils.sysconfig.get_python_inc())

# Set up 'fancy logging' to display messages to the user
from imaspy.setup_logging import connect_formatter

this_file = Path(__file__)
this_dir = this_file.parent.resolve()  # We need to know where we are for many things

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)

logger.info("pyproject.toml support got added in pip 10. Assuming it is available")

###
# HANDLE USER ENVIRONMENT
###
from imaspy.imas_ual_env_parsing import (
    parse_UAL_version_string,
    sanitise_UAL_symver,
    build_UAL_package_name,
)

parser = argparse.ArgumentParser()
parser.add_argument("--build-ual", action="store_true")
args, leftovers = parser.parse_known_args()
fail_on_ual_fail = args.build_ual

# Now that the environment is defined, import the rest of the needed packages
from subprocess import call
import logging
from setuptools import Command, find_packages, setup, Extension
from setup_helpers import prepare_ual_sources, no_cythonize
from distutils.version import LooseVersion
from distutils import sysconfig


# Try to grab all necessary environment variables.
# IMAS_PREFIX points to the directory all IMAS components live in
IMAS_PREFIX = os.getenv("IMAS_PREFIX")
if not IMAS_PREFIX or not os.path.isdir(IMAS_PREFIX):
    logger.warning(
        "IMAS_PREFIX is unset or is not a directory. Points to {!s}. Will not build UAL!".format(
            IMAS_PREFIX
        )
    )
    IMAS_PREFIX = "0.0.0"

# Legacy code, we do not need an explicit IMAS_VERSION.
# What is more important, we need the UAL_VERSION we want to link
# to
## Sanity checks, fallback to 0.0.0_0.0.0
# IMAS_VERSION = os.getenv("IMAS_VERSION")
# if not IMAS_VERSION or not len(IMAS_VERSION.split("."))>2:
#    print('IMAS_VERSION is unset or is not formatted as "0.0.0"')
#    IMAS_VERSION = "0.0.0"
# MAJOR = IMAS_VERSION.split(".")[0]
# MINOR = IMAS_VERSION.split(".")[1]

# Grab the UAL_VERSION to build against
UAL_VERSION = os.getenv("UAL_VERSION")
if not UAL_VERSION:
    logger.warning("UAL_VERSION is unset. Will not build UAL!")
    UAL_VERSION = "0.0.0"

ual_symver, steps_from_version, ual_commit = parse_UAL_version_string(UAL_VERSION)

safe_ual_symver = sanitise_UAL_symver(ual_symver)
ext_module_name = build_UAL_package_name(safe_ual_symver, ual_commit)

# We need source files of the Python HLI UAL library
# to link our build against, the version is grabbed from
# the environment, and they are saved as syubdirectory of
# imaspy
pxd_path = os.path.join(this_dir, "imaspy/_libs")

LANGUAGE = "c"  # Not sure when this is not true
LIBRARIES = "imas"  # We just need the IMAS library
# EXTRALINKARGS = '' # This is machine-specific ignore for now
# EXTRACOMPILEARGS = '' # This is machine-specific ignore for now

###
# Set up Cython build integration
###
### CYTHON COMPILATION ENVIRONMENT

# From https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html#multiple-cython-files-in-a-package
USE_CYTHON = True
cython_like_ext = ".pyx" if USE_CYTHON else ".c"

###
# Build extention list
###
extensions = []

prepare_ual_sources(ual_symver, ual_commit)
import numpy as np

ual_module = Extension(
    name=ext_module_name,
    sources=[
        "imaspy/_libs/_ual_lowlevel.pyx"
    ],  # As these files are copied, easy to find!
    language=LANGUAGE,
    library_dirs=[IMAS_PREFIX + "/lib"],
    libraries=[LIBRARIES],
    # extra_link_args = [ EXTRALINKARGS ],
    # extra_compile_args = [ EXTRACOMPILEARGS ],
    include_dirs=[IMAS_PREFIX + "/include", np.get_include(), pxd_path],
)
if "develop" in sys.argv:
    # Make the dir the .so will be put in
    # Somehow not made automatically
    os.makedirs(ext_module_name.split(".")[0], exist_ok=True)
extensions.append(ual_module)

###
# Set up Cython compilation (or not)
###

if USE_CYTHON:
    try:
        from Cython.Build import cythonize
    except ImportError:
        logger.critical(
            "USE_CYTHON is {!s}, but could not import Cython".format(USE_CYTHON)
        )
    else:
        extensions = cythonize(extensions)
else:
    extensions = no_cythonize(extensions)


with open(os.path.join(this_dir, "README.md"), encoding="utf-8") as file:
    long_description = file.read()

optional_reqs = {}
for req in ["backends_al", "backends_xarray", "core", "examples", "test"]:
    optional_reqs[req] = distutils.text_file.TextFile(
        this_dir / f"requirements_{req}.txt"
    ).readlines()
install_requires = optional_reqs.pop("core")


def get_requires_for_build_wheel(config_settings=None):
    raise Exception("blablabl")


def get_requires_for_build_sdist(config_settings=None):
    raise Exception("blablabl")


setup(
    name="imaspy",
    version="0.0.1",
    packages=find_packages(),
    install_requires=install_requires,
    # Duplicate from pyproject.toml for older setuptools
    setup_requires=["setuptools_scm"],
    author="Karel van de Plassche",
    author_email="karelvandeplassche@gmail.com",
    long_description=long_description,
    url="https://gitlab.com/Karel-van-de-Plassche/imaspy",
    license="MIT",
    classifiers=[
        "Intended Audience :: Science/Research",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
    ],
    extras_require=optional_reqs,
    python_requires=">=3",
    ext_modules=extensions,
    cmdclass={
        "get_requires_for_build_wheel": get_requires_for_build_wheel,
        "get_requires_for_build_sdist": get_requires_for_build_sdist,
    },
)
