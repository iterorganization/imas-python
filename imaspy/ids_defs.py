# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Load IMASPy libs to provide constants
"""

import logging
from typing import Dict, Tuple

from imaspy.setup_logging import root_logger as logger

logger.setLevel(logging.INFO)

try:
    import imas.hli_utils as hli_utils
    from imas.imasdef import (
        ASCII_BACKEND,
        CHAR_DATA,
        CLOSE_PULSE,
        CLOSEST_INTERP,
        DOUBLE_DATA,
        COMPLEX_DATA,
        EMPTY_COMPLEX,
        EMPTY_FLOAT,
        EMPTY_INT,
        FORCE_CREATE_PULSE,
        HDF5_BACKEND,
        IDS_TIME_MODE_HETEROGENEOUS,
        IDS_TIME_MODE_HOMOGENEOUS,
        IDS_TIME_MODE_INDEPENDENT,
        IDS_TIME_MODE_UNKNOWN,
        IDS_TIME_MODES,
        INTEGER_DATA,
        LINEAR_INTERP,
        MDSPLUS_BACKEND,
        MEMORY_BACKEND,
        NODE_TYPE_STRUCTURE,
        OPEN_PULSE,
        PREVIOUS_INTERP,
        READ_OP,
        UDA_BACKEND,
        UNDEFINED_INTERP,
        UNDEFINED_TIME,
        WRITE_OP,
    )
except ImportError as ee:
    logger.critical("IMAS could not be imported. UAL not available! %s", ee)
else:
    # Translation dictionary to go from an ids (primitive) type (without the dimensionality) to a default value
    ids_type_to_default = {
        "STR": "",
        "INT": EMPTY_INT,
        "FLT": EMPTY_FLOAT,
        "CPX": EMPTY_COMPLEX,
    }


DD_TYPES: Dict[str, Tuple[str, int]] = {
    "STR_0D": ("STR", 0),
    "STR_1D": ("STR", 1),
    "str_type": ("STR", 0),
    "str_1d_type": ("STR", 1),
    "flt_type": ("FLT", 0),
    "flt_1d_type": ("FLT", 1),
    "int_type": ("INT", 0),
}

for i in range(0, 7):
    # dimensions are random
    DD_TYPES[f"CPX_{i}D"] = ("CPX", i)
    DD_TYPES[f"FLT_{i}D"] = ("FLT", i)
    if i < 4:
        DD_TYPES[f"INT_{i}D"] = ("INT", i)
