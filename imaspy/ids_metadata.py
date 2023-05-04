# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Core of the IMASPy interpreted IDS metadata
"""
from enum import Enum
from typing import Optional, Any, Dict, Tuple
from xml.etree.ElementTree import Element

from imaspy.ids_coordinates import IDSCoordinate
from imaspy.ids_defs import DD_TYPES
from imaspy.ids_path import IDSPath


class IDSDataType(Enum):
    STRUCTURE = "structure"
    """IDS structure. Maps to an IDSStructure object."""
    STRUCT_ARRAY = "struct_array"
    """IDS array of structures. Maps to an IDSStructArray object with IDSStructure
    children."""
    STR = "STR"
    """String data."""
    INT = "INT"
    """Integer data."""
    FLT = "FLT"
    """Floating point data."""
    CPX = "CPX"
    """Complex data."""


class IDSMetadata:
    """Container for IDS Metadata

    Metadata is everything saved in the attributes of variables in IDSDef.xml.
    This includes for example documentation, its units, and coordinates.
    Metadata is parsed and saved in pythonic types, and used throughout
    IMASPy.
    """

    _init_done = False
    _cache: Dict[Element, "IDSMetadata"] = {}

    def __new__(cls, structure_xml: Element):
        if structure_xml in cls._cache:
            return cls._cache[structure_xml]
        self = super().__new__(cls)
        attrib = structure_xml.attrib

        # Mandatory attributes
        self.name = attrib["name"]

        # These are special and used in IMASPy logic, so we need to ensure proper values
        self.maxoccur = self.parse_maxoccur(attrib.get("maxoccur", "unbounded"))
        self.data_type, self.ndim = self.parse_datatype(attrib.get("data_type", None))
        self.path = IDSPath(attrib.get("path", ""))  # IDSToplevel has no path

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
        self.coordinates = tuple(coors)
        self.coordinates_same_as = tuple(coors_same_as)

        # Store any remaining attributes from the DD XML
        for attr_name in attrib:
            if not hasattr(self, attr_name):
                setattr(self, attr_name, attrib[attr_name])

        self._init_done = True
        cls._cache[structure_xml] = self
        return self

    def __setattr__(self, key: str, value: Any):
        if self._init_done:
            raise RuntimeError("Cannot set attribute: IDSMetadata is read-only.")
        super().__setattr__(key, value)

    def __copy__(self):
        return self  # IDSMetadata is immutable

    def __deepcopy__(self, memo: dict):
        return self  # IDSMetadata is immutable

    def parse_maxoccur(self, value: str) -> Optional[int]:
        """Parse a maxoccur attribute string and return its pythonic value"""
        if value == "unbounded":
            return None
        return int(value)

    def parse_datatype(
        self, data_type: Optional[str]
    ) -> Tuple[Optional[IDSDataType], int]:
        """Parse data type and set self.data_type and self.ndim."""
        if data_type is None:
            return None, 0
        if data_type in DD_TYPES:
            data_type, ndim = DD_TYPES[data_type]
        elif data_type == "structure":
            ndim = 0
        elif data_type == "struct_array":
            ndim = 1
        else:
            raise ValueError(f"Unknown IDS data type: {data_type}")
        return IDSDataType(data_type), ndim
