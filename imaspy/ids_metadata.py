# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Core of the IMASPy interpreted IDS metadata
"""
from typing import Optional, Any, Dict
from xml.etree.ElementTree import Element

from imaspy.ids_coordinates import IDSCoordinate
from imaspy.ids_data_type import IDSDataType
from imaspy.ids_path import IDSPath


class IDSMetadata:
    """Container for IDS Metadata

    Metadata is everything saved in the attributes of variables in IDSDef.xml.
    This includes for example documentation, its units, and coordinates.
    Metadata is parsed and saved in pythonic types, and used throughout
    IMASPy.
    """

    _cache: Dict[Element, "IDSMetadata"] = {}

    def __new__(cls, structure_xml: Element) -> "IDSMetadata":
        if structure_xml not in cls._cache:
            cls._cache[structure_xml] = super().__new__(cls)
        return cls._cache[structure_xml]

    def __init__(self, structure_xml: Element) -> None:
        if hasattr(self, "_init_done"):
            return  # Already initialized, __new__ returned from cache
        attrib = structure_xml.attrib

        # Mandatory attributes
        self.name = attrib["name"]

        # These are special and used in IMASPy logic, so we need to ensure proper values
        self.maxoccur = self.parse_maxoccur(attrib.get("maxoccur", "unbounded"))
        self.data_type, self.ndim = IDSDataType.parse(attrib.get("data_type", None))
        self.path = IDSPath(attrib.get("path", ""))  # IDSToplevel has no path
        self.type = attrib.get("type" , None)  # TODO: parse into an enum?
        """Type of data: "static", "constant", "dynamic" or None"""
        self.timebasepath = attrib.get("timebasepath", "")

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

        # Prevent accidentally modifying attributes
        self._init_done = True

    def __setattr__(self, name: str, value: Any):
        if hasattr(self, "_init_done"):
            raise RuntimeError("Cannot set attribute: IDSMetadata is read-only.")
        super().__setattr__(name, value)

    def __copy__(self):
        return self  # IDSMetadata is immutable

    def __deepcopy__(self, memo: dict):
        return self  # IDSMetadata is immutable

    def parse_maxoccur(self, value: str) -> Optional[int]:
        """Parse a maxoccur attribute string and return its pythonic value"""
        if value == "unbounded":
            return None
        return int(value)
