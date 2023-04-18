# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Core of the IMASPy interpreted IDS metadata
"""
from copy import deepcopy
from typing import Optional, Union, Any
from xml.etree.ElementTree import Element


class IDSMetadata(dict):
    """Container for IDS Metadata

    Metadata is everything saved in the attributes of variables in IDSDef.xml.
    This includes for example documentation, its units, and coordinates.
    Metadata is parsed and saved in pythonic types, and used throughout
    IMASPy.
    """

    def __init__(self, structure_xml: Optional[Element] = None):
        # The user is technically allowed to set attributes to _anything_
        # not necessarily IMASPy-like attributes. These will not be
        # build from a DD, and thus would not have a _structure_xml.
        # Explicitly allow this.
        self.maxoccur = None
        if structure_xml is not None:
            for attr_name, val in structure_xml.attrib.items():
                if attr_name == "maxoccur":
                    self.maxoccur = self.parse_maxoccur(val)
                else:
                    self[attr_name] = val

    def __setattr__(self, key: str, value: Any):
        self[key] = value

    def __getattr__(self, key: str):
        try:
            return self[key]
        except:
            return super().__getattribute__(key)

    def __deepcopy__(self, memo: dict):
        my_copy = {}
        for key, val in self.items():
            my_copy[key] = deepcopy(val)
        return my_copy

    def parse_maxoccur(self, value: str) -> Optional[int]:
        """Parse a maxoccur attribute string and return its pythonic value"""
        if value == "unbounded":
            return None
        return int(value)
