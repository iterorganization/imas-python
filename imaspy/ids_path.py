# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""Logic for interpreting paths to elements in an IDS
"""

import logging
import re
from typing import TYPE_CHECKING, Any, Tuple, Union, List, Iterator, Dict

if TYPE_CHECKING:  # Prevent circular imports
    from imaspy.ids_mixin import IDSMixin


logger = logging.getLogger(__name__)
_IndexType = Union[None, str, int, "IDSPath", slice]
"""Type of an index in a path."""


def _split_on_matching_parens(path: str) -> List[str]:
    """Split a string on matching parentheses ``(``, ``)``.

    Return a list [before_first_(, between(), between)(, ..., after_last)]
    """
    cur_index = 0
    ret = []
    while True:
        next_open = path.find("(", cur_index)
        next_close = path.find(")", cur_index)
        if next_open != -1:
            if next_open > next_close:
                raise ValueError(f"Unmatched parentheses in: {path}")
            ret.append(path[cur_index:next_open])
            # find matching closing bracket
            cur_index = next_open + 1
            next_open = path.find("(", next_open + 1)
            while next_open != -1 and next_open < next_close:
                next_close = path.find(")", next_close + 1)
                if next_close == -1:
                    raise ValueError(f"Unmatched parentheses in: {path}")
                next_open = path.find("(", next_open + 1)
            ret.append(path[cur_index:next_close])
            cur_index = next_close + 1
        else:
            ret.append(path[cur_index:])
            break
    return ret


_number = re.compile(r"\d+", re.ASCII)
_slice = re.compile(r"\d*:\d*", re.ASCII)
_generic_index = re.compile(r"itime|i\d", re.ASCII)
# Naming conventions of DD nodes: start with a-z, a-z, 0-9 and _ allowed, but no
# consecutive double underscores.
_valid_field = re.compile(r"[a-z]([a-z0-9]|_(?!_))*", re.ASCII)


def _parse_path(
    path: str,
) -> Tuple[Tuple[str, ...], Tuple[_IndexType, ...]]:
    """Parse an IDS path into its constituent parts.

    Args:
        path: an IDS path (e.g. ``"profiles_1d(itime)/zeff"``)

    Returns:
        path_parts: all field names, e.g. ``("profiles_1d", "zeff")``
        path_indices: all field indices, e.g. ``("itime", None)``
    """
    path_parts: List[str] = []
    path_indices: List[Union[str, int, "IDSPath", slice]] = []
    split_path = _split_on_matching_parens(path)
    # split_path always has an odd number of items, iterate over pairs first
    for i in range(0, len(split_path) - 1, 2):
        part, index = split_path[i : i + 2]
        if not part:
            raise ValueError(f"Invalid empty node name in path: {path}")
        parts = (part[1:] if part[0] == "/" else part).split("/")
        path_parts.extend(parts)
        path_indices.extend([None] * len(parts))
        if _generic_index.fullmatch(index):
            path_indices[-1] = index  # keep as string
        elif _number.fullmatch(index):
            path_indices[-1] = int(index)
        elif _slice.fullmatch(index):
            start, stop = index.split(":")
            # TODO: currently stores (Fortran-style) 1:3 as slice(1, 3), maybe we should
            # immediately convert it to 0-based Python syntax slice(0, 3). Similarly for
            # explicit indices like (1)
            path_indices[-1] = slice(
                int(start) if start else None,
                int(stop) if stop else None,
            )
        else:  # it must be another path, parse it:
            path_indices[-1] = IDSPath(index)
    if split_path[-1]:
        part = split_path[-1]
        parts = (part[1:] if part[0] == "/" else part).split("/")
        path_parts.extend(parts)
        path_indices.extend([None] * len(parts))
    for part in path_parts:
        if not _valid_field.fullmatch(part):
            raise ValueError(f"Invalid node name '{part}' in path: {path}")
    return tuple(path_parts), tuple(path_indices)


class IDSPath:
    """Represent a path in an IDS.

    An IDS Path indicates the relative position of an element in an IDS and is similar
    to a directory structure.

    Paths consist of elements with an optional index, separated by slashes. For example:

    - ``ids_properties/version_put/data_dictionary``, no indices
    - ``profiles_1d(itime)/zeff``, using a dummy ``itime`` index
    - ``distribution(1)/process(:)/nbi_unit``, using a Fortran-style explicit index (1)
      and Fortran-style range selector (:)
    - ``coordinate_system(process(i1)/coordinate_index)/coordinate(1)`` using another
      IDSPath as index.
    """

    _cache: Dict[str, "IDSPath"] = {}

    def __new__(cls, path: str) -> "IDSPath":
        if path not in cls._cache:
            cls._cache[path] = super().__new__(cls)
        return cls._cache[path]

    def __init__(self, path: str) -> None:
        if hasattr(self, "_init_done"):
            return  # Already initialized, __new__ returned from cache
        self._path = path
        self.parts, self.indices = _parse_path(path)
        self.is_time_path = self.parts and self.parts[-1] == "time"
        # Prevent accidentally modifying attributes
        self._init_done = True

    def __setattr__(self, name: str, value: Any):
        if hasattr(self, "_init_done"):
            raise RuntimeError("Cannot set attribute: IDSPath is read-only.")
        super().__setattr__(name, value)

    def __len__(self) -> int:
        return len(self.parts)

    def __str__(self) -> str:
        return self._path

    def __repr__(self) -> str:
        return f"IDSPath({self._path!r})"

    def __hash__(self) -> int:
        """IDSPaths are immutable, we can be used e.g. as dict key."""
        return hash(self._path)

    def items(self) -> Iterator[Tuple[str, _IndexType]]:
        return zip(self.parts, self.indices)

    def goto(self, from_element: "IDSMixin") -> "IDSMixin":
        """Go to this path, taking from_element as reference.

        This returns the IDSMixin at the specified path, or raises an error when that
        path cannot be found.
        """
        from_path = from_element.metadata.path  # this path doesn't have indices
        element = None
        for i, (part, index) in enumerate(self.items()):
            if isinstance(index, slice):
                raise NotImplementedError("Cannot go to slices")
            if element is None:
                if i < len(from_path) and part == from_path.parts[i]:
                    if index is not None and not isinstance(index, str):
                        logger.warning(
                            "Ignoring index %s while resolving path %s.", index, self
                        )
                else:
                    # last common parent found, set element to it
                    element = from_element
                    for _ in range(len(from_path) - i):
                        element = element._dd_parent
            # Not using `else` on the next line, because element might be set above
            if element is not None:
                element = getattr(element, part)
                if index is not None:
                    if isinstance(index, str):
                        raise ValueError(f"Unexpected index {index} in path '{self}'.")
                    if isinstance(index, IDSPath):
                        val = index.goto(from_element).value
                        if not isinstance(val, int):
                            raise ValueError(f"Invalid index {index} in path '{self}'.")
                        index = val
                    element = element[index - 1]  # path syntax uses 1-based indexing
        return element

    def is_ancestor_of(self, other_path: "IDSPath") -> bool:
        """Test if this path is an ancestor of the other path."""
        len_self = len(self)
        return len_self < len(other_path) and other_path.parts[:len_self] == self.parts
