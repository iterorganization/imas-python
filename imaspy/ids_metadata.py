# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" Core of the IMASPy interpreted IDS metadata
"""
from enum import Enum
from functools import lru_cache
import types
from typing import Optional, Any, Dict
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
    return IDSMetadata(structure_xml)


class IDSMetadata:
    """Container for IDS Metadata

    Metadata is everything saved in the attributes of variables in IDSDef.xml.
    This includes for example documentation, its units, and coordinates.
    Metadata is parsed and saved in pythonic types, and used throughout
    IMASPy.
    """

    def __init__(self, structure_xml: Element) -> None:
        attrib = structure_xml.attrib
        self._structure_xml = structure_xml

        # Mandatory attributes
        self.name = attrib["name"]

        # These are special and used in IMASPy logic, so we need to ensure proper values
        maxoccur = attrib.get("maxoccur", "unbounded")
        self.maxoccur = None if maxoccur == "unbounded" else int(maxoccur)
        self.data_type, self.ndim = IDSDataType.parse(attrib.get("data_type", None))
        self.path_string = attrib.get("path", "")  # IDSToplevel has no path
        self.path = IDSPath(self.path_string)
        self.path_doc = attrib.get("path_doc", "")  # IDSToplevel has no path
        self.type = IDSType(attrib.get("type", None))
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

        # Parse alternative coordinates
        self.alternative_coordinate1 = tuple()
        if "alternative_coordinate1" in attrib:
            self.alternative_coordinate1 = tuple(
                IDSPath(coor)
                for coor in attrib["alternative_coordinate1"].split(";")
            )

        # Store any remaining attributes from the DD XML
        for attr_name in attrib:
            if not hasattr(self, attr_name):
                setattr(self, attr_name, attrib[attr_name])

        # Cache children in a read-only dict
        self._children = types.MappingProxyType({
            xml_child.get("name"): IDSMetadata(xml_child) for xml_child in structure_xml
        })

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
