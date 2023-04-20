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
import os
import site

# Allow importing local files, see https://snarky.ca/what-the-heck-is-pyproject-toml/
import sys
import warnings

# Import other stdlib packages
from itertools import chain
from pathlib import Path

import pkg_resources

# Use setuptools to build packages. Advised to import setuptools before distutils
import setuptools
import tomli
from packaging.version import Version as V
from setuptools import Extension
from setuptools import __version__ as setuptools_version
from setuptools import setup
from setuptools.command.build_py import build_py

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



# We need to know where we are for many things
this_file = Path(__file__)
this_dir = this_file.parent.resolve()

package_name = "imaspy"


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


class build_DD_before_py(build_py):
    """
    Before running build_ext we try to build the DD
    """

    def run(self):
        try:
            prepare_data_dictionaries()
        except:
            logger.warning("Failed to build DD during setup, continuing without.")
        super().run()


if __name__ == "__main__":
    setup(
        zip_safe=False, # https://mypy.readthedocs.io/en/latest/installed_packages.html
        cmdclass={"build_py": build_DD_before_py, "build_DD": BuildDDCommand},
    )
