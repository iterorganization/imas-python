# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Load IMASPy libs to provide constants
"""

import logging
from distutils.version import StrictVersion

from imaspy.logger import logger

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
        IDS_TIME_MODE_INDEPENDENT,
        WRITE_OP,
        CHAR_DATA,
        INTEGER_DATA,
        EMPTY_FLOAT,
        DOUBLE_DATA,
        NODE_TYPE_STRUCTURE,
        CLOSE_PULSE,
        UDA_BACKEND,
        MEMORY_BACKEND,
        HDF5_BACKEND,
        ASCII_BACKEND,
    )

    # TODO: get UAL_VERSION number from hli_utils (if it doesn't exist it's too old)
    # if StrictVersion(hli_utils.__version__) < 10:  # to be defined
    # logger.warning(
    # "Old access layer version detected. The MDSPlus backend will not work with multiple DD versions simultaneously."
    # )
except ImportError:
    logger.critical("IMAS could not be imported. UAL not available!")
else:
    # Translation dictionary to go from an ids (primitive) type (without the dimensionality) to a default value
    ids_type_to_default = {
        "STR": "",
        "INT": EMPTY_INT,
        "FLT": EMPTY_FLOAT,
    }
