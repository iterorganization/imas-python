# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" Load IMASPy libs to provide constants

Backend identifiers
-------------------

The following constants are identifiers for the different Access Layer backends. Please
see the Access Layer documentation for more details on the different backends.

.. data:: ASCII_BACKEND

    Identifier for the ASCII backend.

.. data:: MDSPLUS_BACKEND

    Identifier for the MDS+ backend.

.. data:: HDF5_BACKEND

    Identifier for the HDF5 backend.

.. data:: MEMORY_BACKEND

    Identifier for the memory backend.

.. data:: UDA_BACKEND

    Identifier for the UDA backend.
"""

import functools
import logging

from imaspy.setup_logging import root_logger as logger
from imaspy.imas_interface import imasdef, has_imas

logger.setLevel(logging.INFO)

if has_imas:
    ASCII_BACKEND = imasdef.ASCII_BACKEND
    CHAR_DATA = imasdef.CHAR_DATA
    CLOSE_PULSE = imasdef.CLOSE_PULSE
    CLOSEST_INTERP = imasdef.CLOSEST_INTERP
    CREATE_PULSE = imasdef.CREATE_PULSE
    DOUBLE_DATA = imasdef.DOUBLE_DATA
    COMPLEX_DATA = imasdef.COMPLEX_DATA
    EMPTY_COMPLEX = imasdef.EMPTY_COMPLEX
    EMPTY_FLOAT = imasdef.EMPTY_FLOAT
    EMPTY_INT = imasdef.EMPTY_INT
    ERASE_PULSE = imasdef.ERASE_PULSE
    FORCE_CREATE_PULSE = imasdef.FORCE_CREATE_PULSE
    FORCE_OPEN_PULSE = imasdef.FORCE_OPEN_PULSE
    HDF5_BACKEND = imasdef.HDF5_BACKEND
    IDS_TIME_MODE_HETEROGENEOUS = imasdef.IDS_TIME_MODE_HETEROGENEOUS
    IDS_TIME_MODE_HOMOGENEOUS = imasdef.IDS_TIME_MODE_HOMOGENEOUS
    IDS_TIME_MODE_INDEPENDENT = imasdef.IDS_TIME_MODE_INDEPENDENT
    IDS_TIME_MODE_UNKNOWN = imasdef.IDS_TIME_MODE_UNKNOWN
    IDS_TIME_MODES = imasdef.IDS_TIME_MODES
    INTEGER_DATA = imasdef.INTEGER_DATA
    LINEAR_INTERP = imasdef.LINEAR_INTERP
    MDSPLUS_BACKEND = imasdef.MDSPLUS_BACKEND
    MEMORY_BACKEND = imasdef.MEMORY_BACKEND
    NODE_TYPE_STRUCTURE = imasdef.NODE_TYPE_STRUCTURE
    OPEN_PULSE = imasdef.OPEN_PULSE
    PREVIOUS_INTERP = imasdef.PREVIOUS_INTERP
    READ_OP = imasdef.READ_OP
    UDA_BACKEND = imasdef.UDA_BACKEND
    UNDEFINED_INTERP = imasdef.UNDEFINED_INTERP
    UNDEFINED_TIME = imasdef.UNDEFINED_TIME
    WRITE_OP = imasdef.WRITE_OP
    ASCII_SERIALIZER_PROTOCOL = getattr(imasdef, "ASCII_SERIALIZER_PROTOCOL", 60)
    DEFAULT_SERIALIZER_PROTOCOL = getattr(imasdef, "DEFAULT_SERIALIZER_PROTOCOL", 60)

else:
    # Preset some constants which are used elsewhere
    # this is a bit ugly, perhaps reuse the list of imports from above?
    # it seems no problem to use None, since the use of the values should not
    # be allowed, they are only used in operations which use the backend,
    # which we (should) gate
    ASCII_BACKEND = CHAR_DATA = CLOSE_PULSE = CLOSEST_INTERP = DOUBLE_DATA = None
    FORCE_OPEN_PULSE = CREATE_PULSE = ERASE_PULSE = None
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
    ASCII_SERIALIZER_PROTOCOL = 60
    DEFAULT_SERIALIZER_PROTOCOL = 60


def needs_imas(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not has_imas:
            raise RuntimeError(
                f"Function {func.__name__} requires IMAS, but IMAS is not available."
            )
        return func(*args, **kwargs)

    return wrapper
