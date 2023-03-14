# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Core of the IMASPy interpreted IDS metadata
"""
from copy import deepcopy


class IDSMetadata(dict):
    def __init__(self, structure_xml=None):
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

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, key):
        try:
            return self[key]
        except:
            return super().__getattribute__(key)

    def __deepcopy__(self, memo):
        my_copy = {}
        for key, val in self.items():
            my_copy[key] = deepcopy(val)
        return my_copy

    def parse_maxoccur(self, value):
        maxoccur = None
        try:
            maxoccur = int(value)
        except (ValueError, KeyError):
            pass
        return maxoccur
