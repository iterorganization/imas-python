# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

from packaging.version import Version as _V

from . import _version

__version__ = _version.get_versions()["version"]

version = __version__

# Import logging _first_
from . import setup_logging

# Import main user API objects in the imaspy module
from .db_entry import DBEntry
from .ids_factory import IDSFactory
from .ids_convert import convert_ids

# Load the IMASPy IMAS AL/DD core
from . import (
    db_entry,
    dd_helpers,
    dd_zip,
    mdsplus_model,
    util,
)

OLDEST_SUPPORTED_VERSION = _V("3.22.0")
