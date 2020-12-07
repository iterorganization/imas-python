# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.

from distutils.version import StrictVersion

from imaspy import ids_root, imas_ual_env_parsing, setup_logging
from imaspy.backends import (
    common,
    file_manager,
    ual,
    xarray_core_indexing,
    xarray_core_utils,
)

try:
    from .version import version as __version_from_scm__

    # Set the package version equal to the one grabbed from the
    # Source Management System
    # For git-describe (this repository) it is based on tagged commits
    __version__ = __version_from_scm__
except ModuleNotFoundError:
    # .version may not exist if called from setup.py
    # (through setup_helpers and dd_helpers)
    # don't worry about it in that case
    pass

OLDEST_SUPPORTED_VERSION = StrictVersion("3.21.1")
