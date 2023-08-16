# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.


import logging
import re


logger = logging.getLogger(__name__)
_index_replacement_re = re.compile(r"\((itime|i[0-9]+)\)")
_endswith_index_re = re.compile(r"\((itime|i[0-9]+|(:,?)+)\)(?=[^/])")


class CoordinateLookupError(Exception):
    """Error raised by IDSCoordinate.__getitem__ when a coordinate cannot be found."""

    pass


class ValidationError(Exception):
    """Error raised by IDSToplevel.validate() to indicate the IDS is not valid."""

    pass


class CoordinateError(ValidationError):
    """Error raised by ids.validate() to indicate a coordinate check has failed."""

    def __init__(self, element_path, dimension, size, expected_size, coor_path):
        """Create a new CoordinateError

        Args:
            element_path: path of the element with incorrect size
            dimension: (0-based) dimension with incorrect size
            size: size of element in the given dimension
            expected_size: size of the coordinate for the specified dimension
            coor_path: path of the coordinate, may be None when a coordinate is of fixed
                size (e.g. ``1...3``)
        """
        coor_path_text = ""
        if coor_path is not None:
            coor_path_text = f" (size of coordinate `{coor_path}`)"
        super().__init__(
            f"Dimension {dimension} of element `{element_path}` has incorrect size"
            f" {size}. Expected size is {expected_size}{coor_path_text}."
        )
