# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.

from distutils.version import StrictVersion
import pkg_resources

# First thing for import, try to determine imaspy version
try:
    __version__ = pkg_resources.get_distribution("imaspy").version
except Exception:
    # Try local wrongly install copy
    try:
        from version import __version__
    except Exception:
        # Local copy or not installed with setuptools.
        # Disable minimum version checks on downstream libraries.
        __version__ = "0.0.0"

from imaspy import ids_root, imas_ual_env_parsing, setup_logging
from imaspy.backends import (
    common,
    file_manager,
    ual,
    xarray_core_indexing,
    xarray_core_utils,
)

OLDEST_SUPPORTED_VERSION = StrictVersion("3.21.1")
