# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

from packaging.version import Version as V

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
version = __version__

# Import logging _first_
import logging
from .setup_logging import root_logger as logger

# Hardcode this for stricter imports and debugging
# These imports define the "data containers" for IMASPy.
# We need these to work with data
from . import (
    ids_defs,
    ids_mixin,
    ids_primitive,
    ids_root,
    ids_struct_array,
    ids_structure,
    ids_toplevel,
)

# Import main user API objects in the imaspy module
from .db_entry import DBEntry
from .ids_factory import IDSFactory
from .ids_convert import convert_ids

# Load the IMASPy IMAS AL/DD core
from . import (
    al_exception,
    db_entry,
    dd_helpers,
    dd_zip,
    imas_ual_env_parsing,
    mdsplus_model,
)

OLDEST_SUPPORTED_VERSION = V("3.21.1")
