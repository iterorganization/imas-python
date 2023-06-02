# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.


class ValidationError(Exception):
    """Error raised by IDSToplevel.validate() to indicate the IDS is not valid."""

    pass


class CoordinateError(ValidationError):
    """Error raised by ids.validate() to indicate a coordinate check has failed."""

    def __init__(self, element_path, dimension, size, expected_size, other_path=None):
        other_path_text = ""
        if other_path is not None:
            other_path_text = f" (size of coordinate {other_path})."
        super().__init__(
            f"Dimension {dimension} of element {element_path} has incorrect size"
            f" {size}. Expected size is {expected_size}{other_path_text}."
        )
