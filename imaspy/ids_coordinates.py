import logging
from typing import Any, List, Optional

from imaspy.ids_path import IDSPath


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

    def __init__(self, coordinate_spec: str) -> None:
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

    def __setattr__(self, name: str, value: Any) -> None:
        if self._init_done:
            raise RuntimeError("Cannot set attribute: IDSCoordinate is read-only.")
        super().__setattr__(name, value)

    def __str__(self) -> str:
        return self._coordinate_spec

    def __hash__(self) -> int:
        """IDSCoordinate objects are immutable, we can be used e.g. as dict key."""
        return hash(self._coordinate_spec)
