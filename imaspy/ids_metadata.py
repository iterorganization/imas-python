# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" Core of the IMASPy interpreted IDS metadata
"""
import re
import types
from enum import Enum
from functools import lru_cache
from typing import Any, Optional
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
    """Container for IDS Metadata

    Metadata is everything saved in the attributes of variables in IDSDef.xml.
    This includes for example documentation, its units, and coordinates.
    Metadata is parsed and saved in pythonic types, and used throughout
    IMASPy.

    Metadata of structure (and array of structures) child nodes can be obtained with the
    indexing operator:

    .. code-block:: python

        core_profiles = imaspy.IDSFactory().core_profiles()
        # Get the metadata of the time child of the profiles_1d array of structures
        p1d_time_meta = core_profiles.metadata["profiles_1d/time"]
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
        self.name = attrib["name"]

        # Context path: path relative to the nearest Array of Structures
        if parent_meta is None:  # Toplevel IDS
            self._ctx_path = ""
        elif context_path:
            self._ctx_path = f"{context_path}/{self.name}"
        else:
            self._ctx_path = self.name

        # These are special and used in IMASPy logic, so we need to ensure proper values
        maxoccur = attrib.get("maxoccur", "unbounded")
        self.maxoccur = None if maxoccur == "unbounded" else int(maxoccur)
        self.data_type, self.ndim = IDSDataType.parse(attrib.get("data_type", None))
        self.path_string = attrib.get("path", "")  # IDSToplevel has no path
        self.path = IDSPath(self.path_string)
        self.path_doc = attrib.get("path_doc", "")  # IDSToplevel has no path
        self.type = IDSType(attrib.get("type", None))
        self.timebasepath = attrib.get("timebasepath", "")

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
        self.coordinates = tuple(coors)
        self.coordinates_same_as = tuple(coors_same_as)

        # Parse alternative coordinates
        self.alternative_coordinate1 = tuple()
        if "alternative_coordinate1" in attrib:
            self.alternative_coordinate1 = tuple(
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

    def __getitem__(self, path):
        item = self
        for part in re.split("[./]", path):
            try:
                item = item._children[part]
            except KeyError:
                raise KeyError(
                    f"Invalid path '{path}', '{item.name}' does not have a "
                    f"'{part}' element."
                ) from None
        return item
