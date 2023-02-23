# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Core of the IMASPy interpreted IDS metadata
"""


class Metadata(dict):
    def __init__(self, structure_xml=None):
        # The user is technically allowed to set attributes to _anything_
        # not necessarily IMASPy-like attributes. These will not be
        # build from a DD, and thus would not have a _structure_xml.
        # Explicitly allow this.
        if structure_xml is not None:
            for attr_name, val in structure_xml.attrib.items():
                # setattr(self, attr_name, val)
                self[attr_name] = val

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, key):
        return self[key]
