# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
import difflib
import logging
from typing import TYPE_CHECKING

import imaspy.imas_interface

if TYPE_CHECKING:
    from imaspy.ids_factory import IDSFactory


logger = logging.getLogger(__name__)


# Expose ALException, which may be thrown by the lowlevel
if imaspy.imas_interface.has_imas:
    ALException = imaspy.imas_interface.lowlevel.ALException
else:
    ALException = None


class IDSNameError(ValueError):
    """Error raised by DBEntry.get(_slice) when providing an invalid IDS name."""

    def __init__(self, ids_name: str, factory: "IDSFactory") -> None:
        suggestions = ""
        close_matches = difflib.get_close_matches(ids_name, factory.ids_names(), n=1)
        if close_matches:
            suggestions = f" Did you mean {close_matches[0]!r}?"
        super().__init__(f"IDS {ids_name!r} does not exist.{suggestions}")


class DataEntryException(Exception):
    """Error raised by DBEntry for unexpected data in the backend."""


class MDSPlusModelError(Exception):
    """Error raised when building MDS+ models."""

    def __init__(self, msg: str) -> None:
        super().__init__(f"Error building MDSplus data model: {msg}")


class CoordinateLookupError(Exception):
    """Error raised by IDSCoordinate.__getitem__ when a coordinate cannot be found."""

    pass


class ValidationError(Exception):
    """Error raised by IDSToplevel.validate() to indicate the IDS is not valid."""

    pass


class CoordinateError(ValidationError):
    """Error raised by ids.validate() to indicate a coordinate check has failed."""

    def __init__(self, element_path, dimension, shape, expected_size, coor_path):
        """Create a new CoordinateError

        Args:
            element_path: path of the element with incorrect size
            dimension: (0-based) dimension with incorrect size
            shape: shape of element (e.g. ``(2, 4)``)
            expected_size: size of the coordinate for the specified dimension
            coor_path: path of the coordinate, may be None when a coordinate is of fixed
                size (e.g. ``1...3``)
        """
        if coor_path is not None:  # Error message when coordinate size doesnt match
            details = (
                f"its coordinate in dimension {dimension + 1} (`{coor_path}`) has "
                f"size {expected_size}."
            )
        else:
            details = f"dimension {dimension + 1} must have size {expected_size}."
        super().__init__(
            f"Element `{element_path}` has incorrect shape {shape}: {details}"
        )
