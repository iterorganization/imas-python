# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Load IMASPy libs to provide constants
"""

import logging

from .logger import logger

logger.setLevel(logging.WARNING)

try:
    import imas.hli_utils as hli_utils
    from imas.imasdef import (
        MDSPLUS_BACKEND,
        OPEN_PULSE,
        READ_OP,
        EMPTY_INT,
        FORCE_CREATE_PULSE,
        IDS_TIME_MODE_UNKNOWN,
        IDS_TIME_MODES,
        IDS_TIME_MODE_HOMOGENEOUS,
        IDS_TIME_MODE_HETEROGENEOUS,
        WRITE_OP,
        CHAR_DATA,
        INTEGER_DATA,
        EMPTY_FLOAT,
        DOUBLE_DATA,
        NODE_TYPE_STRUCTURE,
        CLOSE_PULSE,
    )
except ImportError:
    logger.critical("IMASPy _libs could not be imported. UAL not available!")
else:
    # Translation dictionary to go from an ids (primitive) type (without the dimensionality) to a default value
    ids_type_to_default = {
        "STR": "",
        "INT": EMPTY_INT,
        "FLT": EMPTY_FLOAT,
    }
