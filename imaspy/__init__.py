# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.

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

_RAISE_ON_FAILED_INIT = False
# Import logging _first_
import logging
from .setup_logging import root_logger as logger

try:
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
except Exception:
    logger.critical("Global IMASPy __init__ could not import core IDS Python submodules. Trying continuing without IDSs...")
    if _RAISE_ON_FAILED_INIT:
        raise

# Load the IMASPy IMAS AL/DD core
try:
    # Hardcode this for stricter imports and debugging
    # These imports define the "IMAS compatibility" for IMASPy.
    # We need these to work with data in the right format
    from . import (
        al_exception,
        context_store, # todo: Import with side-effects?
        dd_helpers,
        dd_zip,
        imas_ual_env_parsing,
        mdsplus_model,
    )
except Exception:
    logger.critical("Global IMASPy __init__ could not import core IMAS AL/DD Python submodules. Trying continuing without AL/DD...")
    if _RAISE_ON_FAILED_INIT:
        raise
else:
    # Load the IMASPy IMAS AL backend
    # We can do all not-IMAS-AL-backend operations, so we only optionally need this
    try:
        from .backends import (
            ual
        )
    except Exception:
        logger.critical("Global IMASPy __init__ could not import core IMAS AL backend. Trying continuing without IMAS AL...")
    if _RAISE_ON_FAILED_INIT:
        raise

# Load the rest of the IMASPy backends
try:
    # Hardcode this for stricter imports and debugging
    # These backends are partially needed or alpha/beta.
    # We can operate without many of these loaded
    from .backends import (
        common,
        file_manager,
        xarray_core_indexing,
        xarray_core_utils,
    )
except Exception:
    logger.critical("IMASPy __init__ could not import core IMASPy backends. Trying continuing without backends")
    if _RAISE_ON_FAILED_INIT:
        raise

OLDEST_SUPPORTED_VERSION = V("3.21.1")
