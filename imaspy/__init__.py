# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

from packaging.version import Version as V

from . import _version

__version__ = _version.get_versions()["version"]

version = __version__

# Import logging _first_
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
    mdsplus_model,
    util,
)

OLDEST_SUPPORTED_VERSION = V("3.21.1")
