# pylint: disable=wrong-import-position
# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
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
import argparse
import ast
import importlib
import importlib.util
import logging
import warnings
import os
import site

# Allow importing local files, see https://snarky.ca/what-the-heck-is-pyproject-toml/
import sys

# Import other stdlib packages
from itertools import chain
from pathlib import Path

import pkg_resources

# Use setuptools to build packages. Advised to import setuptools before distutils
import setuptools
import tomli
from setuptools import Extension
from setuptools import __version__ as setuptools_version
from setuptools import find_packages, setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.sdist import sdist as _sdist
from setuptools.config import read_configuration

from distutils.sysconfig import get_python_inc as dist_get_python_inc
from distutils.sysconfig import get_python_lib as dist_get_python_lib
from distutils.text_file import TextFile as DistTextFile
from distutils.util import check_environ as dist_check_environ
from distutils.util import get_platform as dist_get_platform
from distutils.version import LooseVersion as V

cannonical_python_command = "module load Python/3.8.6-GCCcore-10.2.0"

if sys.version_info < (3, 7):
    sys.exit(
        "Sorry, Python < 3.7 is not supported. Use a different"
        f" python e.g. '{cannonical_python_command}'"
    )
if sys.version_info < (3, 8):
    warnings.warn("Python < 3.8 support on best-effort basis", FutureWarning)


# Check setuptools version before continuing for legacy builds
if V(setuptools_version) < V("43"):
    raise RuntimeError(
        "Setuptools version outdated. Found"
        f" {V(setuptools_version)} need at least {V('43')}"
    )

# Workaround for https://github.com/pypa/pip/issues/7953
# Cannot install into user site directory with editable source
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]


# Collect env-specific settings
platform = dist_get_platform()  # linux-x86_64
dist_check_environ()

plat_indep_libraries = Path(dist_get_python_lib())
plat_indep_include = Path(dist_get_python_inc())

# We need to know where we are for many things
this_file = Path(__file__)
this_dir = this_file.parent.resolve()

package_name = "imaspy"

# Start: Set up 'fancy logging' to display messages to the user
# Import with side-effects, it sets the root logger
# From https://docs.python.org/3.7/library/importlib.html
setup_logging_file = this_dir / "imaspy/setup_logging.py"
assert setup_logging_file.is_file()
spec = importlib.util.spec_from_file_location("setup_logging", setup_logging_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.modules["imaspy.setup_logging"] = module

logger = logging.getLogger("imaspy")
# End: Setup logging

# Start: Load IMAS user environment
imas_ual_env_parsing_file = this_dir / "imaspy/imas_ual_env_parsing.py"
assert imas_ual_env_parsing_file.is_file()
spec = importlib.util.spec_from_file_location(
    "imas_ual_env_parsing", imas_ual_env_parsing_file
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.modules["imaspy.imas_ual_env_parsing"] = module
from imaspy.imas_ual_env_parsing import (
    build_UAL_package_name,
    parse_UAL_version_string,
    sanitise_UAL_symver,
)

# End: Load IMAS user environment

# Start: Load setup_helpers
setup_helpers_file = this_dir / "setup_helpers.py"
assert setup_helpers_file.is_file()
spec = importlib.util.spec_from_file_location("setup_helpers", setup_helpers_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.modules["imaspy.setup_helpers"] = module
# End: Load setup_helpers

# Start: Load dd_helpers
# We need exceptions as well
imaspy_exceptions_file = this_dir / "imaspy/imaspy_exceptions.py"
assert imaspy_exceptions_file.is_file()
spec = importlib.util.spec_from_file_location(
    "imaspy_exceptions", imaspy_exceptions_file
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.modules["imaspy.imaspy_exceptions"] = module
imaspy_exceptions_file = this_dir / "imaspy_exceptions.py"

dd_helpers_file = this_dir / "imaspy/dd_helpers.py"
assert dd_helpers_file.is_file()
spec = importlib.util.spec_from_file_location("dd_helpers", dd_helpers_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.modules["imaspy.dd_helpers"] = module
from imaspy.dd_helpers import prepare_data_dictionaries

# End: Load dd_helpers

# Define building of the Data Dictionary as custom build step
class BuildDDCommand(setuptools.Command):
    """A custom command to build the data dictionaries."""

    description = "build IDSDef.zip"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Prepare DDs if they can be git pulled"""
        prepare_data_dictionaries()


# class BuildPyCommand(_build_py):
#    """Subclass the build_py command to also build the DD"""
#
#    def run(self):
#        self.run_command("build_DD")
#        super().run()


class MySdist(_sdist):
    def run(self):
        # Execute the classic clean command
        self.run_command("build_DD")
        super().run()


# Now that the environment is defined, import the rest of the needed packages
# setup.cfg as read by setuptools
setup_cfg = this_dir / "setup.cfg"
assert setup_cfg.is_file()
conf_dict = read_configuration(setup_cfg)

# Also read the toml for later use
pyproject_toml = this_dir / "pyproject.toml"
assert pyproject_toml.is_file()
pyproject_text = pyproject_toml.read_text()
pyproject_data = tomli.loads(pyproject_text)


# Try to grab all necessary environment variables.
# IMAS_PREFIX points to the directory all IMAS components live in
IMAS_PREFIX = os.getenv("IMAS_PREFIX")
if not IMAS_PREFIX or not os.path.isdir(IMAS_PREFIX):
    logger.warning(
        "IMAS_PREFIX is unset or is not a directory. Points to %s. Will not build IMAS Access Layer!",
        IMAS_PREFIX,
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

# Grab the Access Layer version to build against
# Canonically this is stored in UAL_VERSION env variable
# We have fallbacks in case it is not defined
UAL_VERSION = os.getenv("UAL_VERSION", None)
if not UAL_VERSION:
    logger.warning("UAL_VERSION is unset. Falling back to IMASPy versioning")
    UAL_VERSION = "0.0.0"

ual_symver, steps_from_version, ual_commit = parse_UAL_version_string(UAL_VERSION)
safe_ual_symver = sanitise_UAL_symver(ual_symver)
ext_module_name = build_UAL_package_name(safe_ual_symver, ual_commit)

# We need source files of the Python HLI UAL library
# to link our build against, the version is grabbed from
# the environment, and they are saved as subdirectory of
# imaspy
pxd_path = os.path.join(this_dir, "imas")

LANGUAGE = "c"  # Not sure when this is not true
LIBRARIES = "imas"  # We just need the IMAS library
# EXTRALINKARGS = '' # This is machine-specific ignore for now
# EXTRACOMPILEARGS = '' # This is machine-specific ignore for now


###
# Set up Cython build integration
###
### CYTHON COMPILATION ENVIRONMENT

# From https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html#multiple-cython-files-in-a-package
REBUILD_LL = False  # Do not rebuild the LL for now
# TODO: See how much SDCC env we can (re)use
if REBUILD_LL:
    USE_CYTHON = True
    cython_like_ext = ".pyx" if USE_CYTHON else ".c"

    ###
    # Build extention list
    ###
    extensions = []

    setup_helpers.prepare_ual_sources(ual_symver, ual_commit)
    try:
        import numpy as np
    except ImportError:
        logger.critical("REBUILD_LL is %s, but could not import numpy", REBUILD_LL)
    else:
        extensions = []

    ual_module = Extension(
        name=ext_module_name,
        sources=["imas/_ual_lowlevel.pyx"],  # As these files are copied, easy to find!
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
                "USE_CYTHON is %s, but could not import Cython",
                USE_CYTHON,
            )
        else:
            extensions = cythonize(extensions)
    else:
        extensions = setup_helpers.no_cythonize(extensions)
else:
    extensions = []

if __name__ == "__main__":
    # Legacy setuptools support, e.g. `python setup.py something`
    # See [PEP-0517](https://www.python.org/dev/peps/pep-0517/) and
    # [setuptools docs](https://setuptools.readthedocs.io/en/latest/userguide/quickstart.html#basic-use)
    # Rough logic setuptools_scm
    # See https://pypi.org/project/setuptools-scm/
    # For allowed version strings, see https://packaging.python.org/specifications/core-metadata/ for allow version strings

    setup(
        setup_requires=pyproject_data["build-system"]["requires"],
        # cmdclass={"build_py": BuildPyCommand, "build_DD": BuildDDCommand, "sdist": MySdist},
        cmdclass={"build_DD": BuildDDCommand, "sdist": MySdist},
    )
