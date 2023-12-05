# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" Core of the IMASPy interpreted IDS metadata
"""
from enum import Enum
from functools import lru_cache
import types
from typing import Optional, Any
from xml.etree.ElementTree import Element

from imaspy.ids_coordinates import IDSCoordinate
from imaspy.ids_data_type import IDSDataType
from imaspy.ids_path import IDSPath


class IDSType(Enum):
    """Data dictionary indication of the time-variation character of a DD node

    The Data Model distinguishes between categories of data according to their
    time-variation. ``constant`` data are data which are not varying within the context
    of the data being referred to (e.g. pulse, simulation, calculation); ``static`` data
    are likely to be constant over a wider range (e.g. nominal coil positions during
    operation); ``dynamic`` data are those which vary in time within the context of the
    data.

    As in the Python HLI, IMASPy only distinguishes between dynamic and non-dynamic
    nodes.
    """

    NONE = None
    """The DD node has no type attribute.
    """

    DYNAMIC = "dynamic"
    """Data that is varying in time.
    """

    CONSTANT = "constant"
    """Data that does not vary within the IDS.
    """

    STATIC = "static"
    """Data that does not vary between multiple IDSs.
    """

    def __init__(self, name):
        self.is_dynamic = name == "dynamic"


# This cache is for IDSMetadata for IDS toplevels
# Typical use case is one or two DD versions
# Currently the DD has ~70 unique IDSs, so this cache has plenty of size to store all
# IDSs of two DD versions.
#
# Perhaps the cache could be smaller, but that would be less efficient for the unit
# tests...
@lru_cache(maxsize=256)
def get_toplevel_metadata(structure_xml):
    return IDSMetadata(structure_xml, "", None)


class IDSMetadata:
    """Container for IDS Metadata stored in the Data Dictionary.

    Metadata is everything saved in the attributes of variables in IDSDef.xml.
    This includes for example documentation, its units, and coordinates.
    """

    def __init__(
        self,
        structure_xml: Element,
        context_path: str,
        parent_meta: Optional["IDSMetadata"],
    ) -> None:
        attrib = structure_xml.attrib
        self._structure_xml = structure_xml
        self._parent = parent_meta

        # Mandatory attributes
        self.name: str = attrib["name"]
        """Name of the IDS node, for example ``"comment"``."""

        # Context path: path relative to the nearest Array of Structures
        if parent_meta is None:  # Toplevel IDS
            self._ctx_path = ""
        elif context_path:
            self._ctx_path = f"{context_path}/{self.name}"
        else:
            self._ctx_path = self.name

        # These are special and used in IMASPy logic, so we need to ensure proper values
        maxoccur = attrib.get("maxoccur", "unbounded")
        self.maxoccur: Optional[int] = None if maxoccur == "unbounded" else int(maxoccur)
        """Maximum number of occurrences allowed in the MDS+ backend. Applies to IDS
        toplevels and Arrays of Structures."""
        self.data_type: IDSDataType
        """Data type of the IDS node."""
        self.ndim: int
        """Number of dimensions (rank) of the IDS node."""
        self.data_type, self.ndim = IDSDataType.parse(attrib.get("data_type", None))
        self.path_string: str = attrib.get("path", "")  # IDSToplevel has no path
        """Path of this IDS node from the IDS toplevel, for example
        ``"ids_properties/comment"``."""
        self.path: IDSPath = IDSPath(self.path_string)
        """Parsed path of this IDS node from the IDS toplevel, see also
        :py:attr:`path_string`."""
        self.path_doc: str = attrib.get("path_doc", "")  # IDSToplevel has no path
        """Path of this IDS node from the IDS toplevel, as shown in the Data Dictionary
        documentation. For example ``"time_slice(itime)/profiles_2d(i1)/r(:,:)"``."""
        self.type: IDSType = IDSType(attrib.get("type", None))
        """Type of the IDS node, indicating if this node is time dependent. Possible
        values are ``dynamic`` (i.e. time-dependent), ``constant`` and ``static``."""
        self.timebasepath = attrib.get("timebasepath", "")
        self.units: str = attrib.get("units", "")
        """Units of this IDS node. For example ``"m.s^-2"``."""
        if self.units == "as_parent" and parent_meta is not None:
            self.units = parent_meta.units

        # timebasepath is not always defined in the DD XML, mainly not for struct_arrays
        # Also, when it is defined, it may not be correct (DD 3.39.0)
        if self.data_type is IDSDataType.STRUCT_ARRAY:
            # https://git.iter.org/projects/IMAS/repos/access-layer/browse/pythoninterface/py_ids.xsl?at=refs%2Ftags%2F4.11.4#367-384
            if self.type.is_dynamic:
                self.timebasepath = self._ctx_path + "/time"
            else:
                self.timebasepath = ""
        else:  # IDSPrimitive
            # https://git.iter.org/projects/IMAS/repos/access-layer/browse/pythoninterface/py_ids.xsl?at=refs%2Ftags%2F4.11.4#1524-1566
            if self.timebasepath and (
                not self.type.is_dynamic or self._parent._is_dynamic
            ):
                self.timebasepath = ""
        self._is_dynamic = self.type.is_dynamic
        if self._parent is not None:
            self._is_dynamic = self._is_dynamic or self._parent._is_dynamic

        # Parse coordinates
        coors = [IDSCoordinate("")] * self.ndim
        coors_same_as = [IDSCoordinate("")] * self.ndim
        for dim in range(self.ndim):
            coor = f"coordinate{dim + 1}"
            if coor in attrib:
                coors[dim] = IDSCoordinate(attrib[coor])
                setattr(self, coor, coors[dim])
            if coor + "_same_as" in attrib:
                coors_same_as[dim] = IDSCoordinate(attrib[coor + "_same_as"])
                setattr(self, coor + "_same_as", coors_same_as[dim])
        self.coordinates: "tuple[IDSCoordinate]" = tuple(coors)
        """Tuple of coordinates of this node.

        ``coordinates[0]`` is the coordinate of the first dimension, etc."""
        self.coordinates_same_as: "tuple[IDSCoordinate]" = tuple(coors_same_as)
        """Indicates quantities which share the same coordinate in a given dimension,
        but the coordinate is not explicitly stored in the IDS."""

        # Parse alternative coordinates
        self.alternative_coordinates: "tuple[IDSPath]" = tuple()
        """Quantities that can be used as coordinate instead of this node."""
        if "alternative_coordinate1" in attrib:
            self.alternative_coordinates = tuple(
                IDSPath(coor) for coor in attrib["alternative_coordinate1"].split(";")
            )

        # Store any remaining attributes from the DD XML
        for attr_name in attrib:
            if not hasattr(self, attr_name):
                setattr(self, attr_name, attrib[attr_name])

        # Cache children in a read-only dict
        ctx_path = "" if self.data_type is IDSDataType.STRUCT_ARRAY else self._ctx_path
        self._children = types.MappingProxyType(
            {
                xml_child.get("name"): IDSMetadata(xml_child, ctx_path, self)
                for xml_child in structure_xml
            }
        )

        # Prevent accidentally modifying attributes
        self._init_done = True

    def __repr__(self) -> str:
        return f"<IDSMetadata for '{self.name}'>"

    def __setattr__(self, name: str, value: Any):
        if hasattr(self, "_init_done"):
            raise RuntimeError("Cannot set attribute: IDSMetadata is read-only.")
        super().__setattr__(name, value)

    def __copy__(self):
        return self  # IDSMetadata is immutable

    def __deepcopy__(self, memo: dict):
        return self  # IDSMetadata is immutable
