# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.


import logging
from typing import Dict
import re


logger = logging.getLogger(__name__)
_index_replacement_re = re.compile(r"\((itime|i[0-9]+)\)")
_endswith_index_re = re.compile(r"\((itime|i[0-9]+|(:,?)+)\)(?=[^/])")


class CoordinateLookupError(Exception):
    """Error raised by IDSCoordinate.__getitem__ when a coordinate cannot be found."""

    pass


class ValidationError(Exception):
    """Error raised by IDSToplevel.validate() to indicate the IDS is not valid."""

    def __init__(self, msg: str, aos_indices: Dict[str, int]) -> None:
        """Create a new ValidationError

        ValidationError automatically converts path indices contained in the message to
        their Python equivalent.

        Args:
            msg: Error description
            aos_indices: Mapping of AoS indices to values

        Example:

            >>> aos_indices = {'itime': 2, 'i1': 4}
            >>> ValidationError("Path: `profiles_1d(itime)/ion(i1)/label`", aos_indices)
            ValidationError('Path: `profiles_1d[2].ion[4].label`')
        """
        self._msg = msg
        try:
            msg = _endswith_index_re.sub("", msg)  # Remove index at the end of the path
            msg = _index_replacement_re.sub(r"[{\1}]", msg).format_map(aos_indices)
            msg = msg.replace('/', '.')  # Replace / in paths by .
        except Exception:
            # Log but ignore errors
            logger.error(
                "Error while formatting message %s with aos_indices %s",
                msg,
                aos_indices,
                exc_info=1,
            )
        super().__init__(msg)


class CoordinateError(ValidationError):
    """Error raised by ids.validate() to indicate a coordinate check has failed."""

    def __init__(
        self, element_path, dimension, size, expected_size, other_path, aos_indices
    ):
        other_path_text = ""
        if other_path is not None:
            other_path_text = f" (size of coordinate `{other_path}`)"
        super().__init__(
            f"Dimension {dimension} of element `{element_path}` has incorrect size"
            f" {size}. Expected size is {expected_size}{other_path_text}.",
            aos_indices,
        )
