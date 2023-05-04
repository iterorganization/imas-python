# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
"""Logic for interpreting coordinates in an IDS
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np

from imaspy.ids_path import IDSPath

if TYPE_CHECKING:  # Prevent circular imports
    from imaspy.ids_mixin import IDSMixin
    from imaspy.ids_primitive import IDSPrimitive

logger = logging.getLogger(__name__)


class IDSCoordinate:
    """Class representing a coordinate reference from the DD.

    Examples:
    - Coordinates are an index:
      - "1...N": any number of items allowed
      - "1...3": max 3 items allowed
    - Coordinates refer to other quantities:
      - "time": refers to the "time" quantity in the IDS toplevel
      - "profiles_1d(itime)/time": refers to the "time" quantity in the
        profiles_1d IDSStructArray with (dummy) index itime
    - Coordinates specify alternatives:
      - "distribution(i1)/profiles_2d(itime)/grid/r OR
        distribution(i1)/profiles_2d(itime)/grid/rho_tor_norm": coordinate can be "r" or
        "rho_tor_norm" (only one may be filled)
      - "coherent_wave(i1)/beam_tracing(itime)/beam(i2)/length OR 1...1": either use
        "length" as coordinate, or this dimension must have size one.
    """

    _init_done = False
    _cache: Dict[str, "IDSCoordinate"] = {}

    def __new__(cls, coordinate_spec: str) -> "IDSCoordinate":
        if coordinate_spec in cls._cache:
            return cls._cache[coordinate_spec]
        self = super().__new__(cls)
        self._coordinate_spec = coordinate_spec
        self.max_size: Optional[int] = None

        refs: List[IDSPath] = []
        specs = coordinate_spec.split(" OR ")
        for spec in specs:
            if spec.startswith("1..."):
                if spec != "1...N":
                    try:
                        self.max_size = int(spec[4:])
                    except ValueError:
                        logger.debug(
                            f"Ignoring invalid coordinate specifier {spec}",
                            exc_info=True,
                        )
            elif spec:
                try:
                    refs.append(IDSPath(spec))
                except ValueError:
                    logger.debug(
                        f"Ignoring invalid coordinate specifier {spec}", exc_info=True
                    )
        self.references = tuple(refs)
        num_rules = len(self.references) + (self.max_size is not None)
        self.has_validation = num_rules > 0
        self.has_alternatives = num_rules > 1
        self.is_time_coordinate = any(ref.is_time_path for ref in self.references)
        self._init_done = True
        cls._cache[coordinate_spec] = self
        return self

    def __setattr__(self, name: str, value: Any) -> None:
        if self._init_done:
            raise RuntimeError("Cannot set attribute: IDSCoordinate is read-only.")
        super().__setattr__(name, value)

    def __str__(self) -> str:
        return self._coordinate_spec

    def __hash__(self) -> int:
        """IDSCoordinate objects are immutable, we can be used e.g. as dict key."""
        return hash(self._coordinate_spec)


class IDSCoordinates:
    """Class representing coordinates of an IDSMixin.

    Can be used to automatically retrieve coordinate values.
    """

    def __init__(self, mixin: "IDSMixin") -> None:
        self._mixin = mixin

    def __len__(self) -> int:
        """Number of coordinates is equal to the dimension of the bound IDSMixin."""
        return self._mixin.metadata.ndim

    def __getitem__(self, key: int) -> Union["IDSPrimitive", np.ndarray]:
        """Get the coordinate of the given dimension.

        When the coordinate is an index (e.g. 1...N) this will return an numpy arange
        with the same size as the data currently has in that dimension.

        When one coordinate path is defined in the DD, the corresponding IDSPrimitive
        object is returned.

        When multiple coordinate paths are defined, the one that is set is returned. A
        ValueError is raised when multiple or none are defined.1
        """
        coordinate = self._mixin.metadata.coordinates[key]
        if not coordinate.references:
            return np.arange(self._mixin.value.shape[key])
        if not coordinate.has_alternatives:
            return coordinate.references[0].goto(self._mixin)
        refs = [ref.goto(self._mixin) for ref in coordinate.references]
        ref_is_defined = [len(ref.value) > 0 for ref in refs]
        if sum(ref_is_defined) == 0:
            if coordinate.max_size is not None:
                # alternatively we can be an index
                return np.arange(self._mixin.value.shape[key])
            raise RuntimeError(
                "Cannot get coordinate: none of the alternative coordinate options "
                f"{coordinate.references} are set."
            )
        if sum(ref_is_defined) == 1:
            for i in range(len(refs)):
                if ref_is_defined[i]:
                    return refs[i]
        raise RuntimeError(
            "Cannot get coordinate: multiple alternative coordinate options are set."
        )

    @property
    def time_index(self) -> Optional[int]:
        """Get the index of the time coordinate, or None if there is no time coordinate.
        """
        for i, coor in enumerate(self._mixin.metadata.coordinates):
            if coor.is_time_coordinate:
                return i
        return None
