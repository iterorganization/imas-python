# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" Load IMASPy libs to provide constants
"""

import functools
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

    HAS_IMAS = True
except ImportError as ee:
    logger.critical("IMAS could not be imported. UAL not available! %s", ee)
    HAS_IMAS = False

    # Preset some constants which are used elsewhere
    # this is a bit ugly, perhaps reuse the list of imports from above?
    # it seems no problem to use None, since the use of the values should not
    # be allowed, they are only used in operations which use the backend,
    # which we (should) gate
    hli_utils = None
    ASCII_BACKEND = CHAR_DATA = CLOSE_PULSE = CLOSEST_INTERP = DOUBLE_DATA = None
    COMPLEX_DATA = FORCE_CREATE_PULSE = HDF5_BACKEND = None
    INTEGER_DATA = LINEAR_INTERP = MDSPLUS_BACKEND = MEMORY_BACKEND = None
    NODE_TYPE_STRUCTURE = OPEN_PULSE = PREVIOUS_INTERP = READ_OP = None
    UDA_BACKEND = UNDEFINED_INTERP = UNDEFINED_TIME = WRITE_OP = None
    # These constants are also useful when not working with the UAL
    EMPTY_FLOAT = -9e40
    EMPTY_INT = -999_999_999
    EMPTY_COMPLEX = complex(EMPTY_FLOAT, EMPTY_FLOAT)
    IDS_TIME_MODE_UNKNOWN = EMPTY_INT
    IDS_TIME_MODE_HETEROGENEOUS = 0
    IDS_TIME_MODE_HOMOGENEOUS = 1
    IDS_TIME_MODE_INDEPENDENT = 2
    IDS_TIME_MODES = [0, 1, 2]

try:
    # Since serialisation is a HLI-feature for now we can always enable it
    from imas.imasdef import ASCII_SERIALIZER_PROTOCOL, DEFAULT_SERIALIZER_PROTOCOL
except ImportError:
    ASCII_SERIALIZER_PROTOCOL = 60
    DEFAULT_SERIALIZER_PROTOCOL = 60


def needs_imas(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not HAS_IMAS:
            raise RuntimeError(
                f"Function {func.__name__} requires IMAS, but IMAS is not available."
            )
        return func(*args, **kwargs)

    return wrapper
