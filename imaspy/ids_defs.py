# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Load IMASPy libs to provide constants
"""

import logging

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
    
    # Preset some constants which are used elsewhere
    # this is a bit ugly, perhaps reuse the list of imports from above?
    # it seems no problem to use None, since the use of the values should not
    # be allowed, they are only used in operations which use the backend,
    # which we (should) gate
    ASCII_BACKEND = CHAR_DATA = CLOSE_PULSE = CLOSEST_INTERP = DOUBLE_DATA = EMPTY_FLOAT = EMPTY_INT = FORCE_CREATE_PULSE = HDF5_BACKEND = IDS_TIME_MODE_HETEROGENEOUS = IDS_TIME_MODE_HOMOGENEOUS = IDS_TIME_MODE_INDEPENDENT = IDS_TIME_MODE_UNKNOWN = IDS_TIME_MODES = INTEGER_DATA = LINEAR_INTERP = MDSPLUS_BACKEND = MEMORY_BACKEND = NODE_TYPE_STRUCTURE = OPEN_PULSE = PREVIOUS_INTERP = READ_OP = UDA_BACKEND = UNDEFINED_INTERP = UNDEFINED_TIME = WRITE_OP = None
else:
    # Translation dictionary to go from an ids (primitive) type (without the dimensionality) to a default value
    ids_type_to_default = {
        "STR": "",
        "INT": EMPTY_INT,
        "FLT": EMPTY_FLOAT,
    }

try:
    # serialization may not be present in the installed imas library
    from imas.imasdef import ASCII_SERIALIZER_PROTOCOL, DEFAULT_SERIALIZER_PROTOCOL
    IMAS_HAS_SERIALIZATION = True
except ImportError:
    ASCII_SERIALIZER_PROTOCOL = -1
    DEFAULT_SERIALIZER_PROTOCOL = -2
    IMAS_HAS_SERIALIZATION = False


DD_TYPES = {
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
    DD_TYPES["FLT_%dD" % i] = ("FLT", i)
    if i < 4:
        DD_TYPES["INT_%dD" % i] = ("INT", i)
