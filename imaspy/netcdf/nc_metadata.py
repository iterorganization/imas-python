# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""NetCDF metadata for dimensions and tensorization of IDSs.
"""

from functools import lru_cache
from typing import Dict, List, Optional, Set, Tuple

from imaspy.ids_data_type import IDSDataType
from imaspy.ids_metadata import IDSMetadata


class NCMetadata:
    """NCMetadata contains additional netCDF metadata for an IDS data structure.

    When constructing an NCMetadata, the complete IDS structure is scanned and all DD
    coordinate information is parsed. This information is used to construct netCDF
    dimension information for all quantities in the IDS.

    Coordinate parsing is done in three phases:

    1.  Traverse the full metadata tree and parse coordinate information for all
        quantities. See ``_parse()`` and ``_parse_dimensions()``.
    2.  Resolve shared dimensions. See ``_resolve_pending()``.
    3.  Tensorize all quantities. See ``_tensorize_dimensions()``.
    """

    def __init__(self, ids_metadata: IDSMetadata) -> None:
        if ids_metadata._parent is not None:
            raise ValueError("Toplevel IDS metadata is required.")

        self.ids_metadata = ids_metadata
        """Metadata of the IDS toplevel that this NC metadata is for."""
        self.time_dimensions: Set[str] = set()
        """Set of all (inhomogeneous) time dimensions."""
        self.dimensions: Dict[str, List[str]] = {}
        """Mapping of paths to dimension names."""
        self.coordinates: Dict[str, List[str]] = {}
        """Mapping of paths to coordinate variable names."""
        self.aos: Dict[str, str] = {}
        """Mapping of paths to their nearest AoS parent."""

        # Temporary variables for parsing coordinates
        #   Pending coordinate references
        self._pending = {}  # (path, dimension): (coordinate_path, coordinate_dimension)
        #   Dimensions before tensorization
        self._ut_dims = {}  # path: [dim1, dim2, ...]
        #   Coordinates before tensorization
        self._ut_coords = {}  # path: [coor1, coor2, ...]

        # Parse the whole metadata tree
        self._parse(ids_metadata, None, 0)
        try:
            self._resolve_pending()
        except RecursionError:
            raise RuntimeError(
                "Unable to resolve data dictionary coordinates, does the DD contain"
                " circular coordinate references?"
            ) from None
        self._tensorize_dimensions()
        # Delete temporary variables
        del self._pending, self._ut_dims, self._ut_coords

        # Sanity check:
        assert len(self.dimensions) == len(set(self.dimensions))

        self.time_coordinates: Set[str] = {
            dimension.partition(":")[0] for dimension in self.time_dimensions
        }
        """All coordinate variable names representing (inhomogeneous) time."""

        # Add cache for public API
        self.get_dimensions = lru_cache(maxsize=None)(self.get_dimensions)

    def get_coordinates(self, path: str, homogeneous_time: bool) -> str:
        """Get the coordinate string (adhering to CF conventions) for a netCDF variable.

        Args:
            path: Data Dictionary path to the variable, e.g. ``ids_properties/comment``.
            homogeneous_time: Use homogeneous time coordinates. When True,
                ``ids_properties.homogeneous_time`` should be set to ``1``.
        """
        if path not in self.coordinates:
            return ""

        if not homogeneous_time:
            return " ".join(self.coordinates[path])

        # Replace inhomogeneous time coordinates with root time:
        return " ".join(
            "time" if coord in self.time_coordinates else coord
            for coord in self.coordinates[path]
        )

    def get_dimensions(self, path: str, homogeneous_time: bool) -> Tuple[str]:
        """Get the dimensions for a netCDF variable.

        Args:
            path: Data Dictionary path to the variable, e.g. ``ids_properties/comment``.
            homogeneous_time: Use homogeneous time coordinates. When True,
                ``ids_properties.homogeneous_time`` should be set to ``1``.
        """
        if path not in self.dimensions:
            return []

        if not homogeneous_time:
            return tuple(self.dimensions[path])

        # Replace inhomogeneous time dimensions with root time:
        return tuple(
            "time" if dim in self.time_dimensions else dim
            for dim in self.dimensions[path]
        )

    def _parse(
        self, metadata: IDSMetadata, parent_aos: Optional[str], aos_level: int
    ) -> None:
        """Recursively parse DD coordinates."""
        for child in metadata._children.values():
            if parent_aos:
                self.aos[child.path_string] = parent_aos
            if child.data_type is IDSDataType.STRUCTURE:
                self._parse(child, parent_aos, aos_level)
            elif child.ndim:
                self._parse_dimensions(child, aos_level)
                if child.data_type is IDSDataType.STRUCT_ARRAY:
                    self._parse(child, child.path_string, aos_level + 1)
            else:
                self._ut_dims[child.path_string] = []

    def _parse_dimensions(self, metadata: IDSMetadata, aos_level: int) -> None:
        """Parse dimensions and auxiliary coordinates from DD coordinate metadata.

        DD coordinates come in different flavours (see also
        :mod:`imaspy.ids_coordinates`), which we handle in this function:

        1.  Coordinate is an index.

            This is expressed in the Data Dictionary as ``coordinateX=1...N``, where
            ``N`` can be an integer indicating the exact size of the dimension, or a
            literal ``N`` when the dimension is unbounded.

            Such an index will become its own netCDF dimension.

        2.  Coordinate shares a dimension with another variable, but there is no
            explicit coordinate variable in the DD.

            This is expressed in the Data Dictionary as ``coordinateX=1...N`` (like in
            case 1), but in addition there is an attribute ``coordinateX_same_as=...``
            which indicates the variable it shares its dimension with.

        3.  Coordinate refers to another quantity in the DD.

            This is expressed in the Data Dictionary as ``coordinateX=quantity`` which
            indicates the variable that is the coordinate. Note that a time coordinate
            is treated specially, see below.

            a.  Starting in Data Dictionary version 4.0.0, the coordinate quantity can
                indicate that there are alternatives for itself. This is expressed as
                ``alternative_coordinate1=quantity1;quantity2;...``.

                This case is not yet implemented.

        4.  Coordinate refers to multiple other quantities in the DD.

            This is expressed in the Data Dictionary as ``coordinateX=quantity1 OR
            quantity2 [OR ...]``. This case is not yet implemented.

        Notes:

        -   It is assumed that there are no circular coordinate references, i.e. no two
            quantities in the Data Dictionary point to eachother as a coordinate.
        -   Time dimensions and coordinate names are recorded separately. When using
            homogeneous_time, all time coordinates point to the root ``time`` quantity
            instead of the quantity recorded in the coordinate properties.
        """
        dimensions = []
        coordinates = []
        for i, coord in enumerate(metadata.coordinates):
            dim_name = None
            if not coord.references:
                same_as = metadata.coordinates_same_as[i]
                if same_as.references:
                    # ------ CASE 2: coordinate is same as another ------
                    # Put reference in pending to be resolved in second pass
                    coordinate_path = "/".join(same_as.references[0].parts)
                    self._pending[(metadata.path_string, i)] = (coordinate_path, i)

                else:
                    # ------ CASE 1: coordinate is an index ------
                    # Create a new dimension
                    dim_name = metadata.path_string.replace("/", ".")
                    if (
                        aos_level + metadata.ndim != 1
                        and metadata.data_type is not IDSDataType.STRUCT_ARRAY
                    ):
                        # This variable is >1D after tensorization, so we cannot use our
                        # path as dimension name:
                        dim_name = f"{dim_name}:{i}"

            elif len(coord.references) == 1:
                # ------ CASE 3: refers to another quantity in the DD ------
                if metadata.path.is_ancestor_of(coord.references[0]):
                    # Coordinate is inside this AoS (and must be 0D): create dimension
                    # E.g. core_profiles IDS: profiles_1d -> profiles_1d/time
                    dim_name = ".".join(coord.references[0].parts)

                else:
                    # Put reference in pending to be resolved in second pass
                    coordinate_path = "/".join(coord.references[0].parts)
                    self._pending[(metadata.path_string, i)] = (coordinate_path, 0)
                    coordinates.append(coordinate_path.replace("/", "."))

            else:
                # ------ CASE 3: refers to multiple other quantities in the DD ------
                raise NotImplementedError(
                    "Alternative coordinates are not yet supported"
                )

            dimensions.append(dim_name)
            if dim_name is not None and coord.is_time_coordinate:
                # Record time dimension
                self.time_dimensions.add(dim_name)

        # Store untensorized dimensions and coordinates
        self._ut_dims[metadata.path_string] = dimensions
        if coordinates:
            self._ut_coords[metadata.path_string] = coordinates

    def _resolve_pending(self):
        """Resolve all pending dimension references."""
        pending_items = self._pending.items()
        self._pending = {}

        for (path, dimension), (coor_path, coor_dimension) in pending_items:
            dim = self._ut_dims[coor_path][coor_dimension]
            if dim is None:
                # We refer to a (still) unresolved coordinate, put back in the queue:
                self._pending[(path, dimension)] = (coor_path, coor_dimension)
            else:
                # Reference is resolved:
                self._ut_dims[path][dimension] = dim

        # If we have any pending left, try to resolve them again.
        # Note: if there are circular references we cannot resolve them, and this will
        # at some point raise a RecursionError. This error is caught in __init__() and a
        # more meaningful exception is raised instead.
        if self._pending:
            self._resolve_pending()

    def _tensorize_dimensions(self):
        """Create the final tensorized data structures.

        This prepends all dimensions (coordinates) with the dimensions (coordinates) of
        their ancestor Array of Structures.
        """
        for path in self._ut_dims:
            aos_dims = aos_coords = []
            aos = self.aos.get(path)
            if aos is not None:
                # Note: by construction of self._ut_dims, we know that ancestor AOSs are
                # always handled before their children. self.dimensions[aos] must
                # therefore exist:
                aos_dims = self.dimensions[aos]
                aos_coords = self.coordinates.get(aos, [])
            self.dimensions[path] = aos_dims + self._ut_dims[path]
            if aos_coords or path in self._ut_coords:
                self.coordinates[path] = aos_coords + self._ut_coords.get(path, [])
