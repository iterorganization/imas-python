# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" A structure in an IDS

* :py:class:`IDSStructure`
"""

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

import logging
from typing import Dict
from xml.etree.ElementTree import Element

from imaspy.setup_logging import root_logger as logger
from imaspy.ids_metadata import IDSDataType
from imaspy.ids_mixin import IDSMixin
from imaspy.ids_primitive import create_leaf_container


class IDSStructure(IDSMixin):
    """IDS structure node

    Represents a node in the IDS tree. Does not itself contain data,
    but contains references to leaf nodes with data (IDSPrimitive) or
    other node-like structures, for example other IDSStructures or
    IDSStructArrays
    """

    _MAX_OCCURRENCES = None
    _convert_ids_types = False

    def __init__(self, parent: IDSMixin, structure_xml: Element):
        """Initialize IDSStructure from XML specification

        Initializes in-memory an IDSStructure. The XML should contain
        all direct descendants of the node. To avoid duplication,
        none of the XML structure is saved directly, so this transformation
        might be irreversible.

        Args:
            parent: Parent structure. Can be anything, but at database write
                time should be something with a path attribute
            structure_xml: Object describing the structure of the IDS. Usually
                an instance of `xml.etree.ElementTree.Element`
        """
        # To ease setting values at this stage, do not try to cast values
        # to canonical forms
        # Since __setattr__ looks for _convert_ids_types we set it through __dict__
        self.__dict__["_convert_ids_types"] = False
        super().__init__(parent, structure_xml=structure_xml)

        self._children = []  # Store the children as a list of strings.
        # Loop over the direct descendants of the current node.
        # Do not loop over grandchildren, that is handled by recursiveness.

        if logger.level <= logging.DEBUG:
            log_string = " " * self.depth + " - % -38s initialization"

        for child in structure_xml:
            my_name = child.get("name")
            if logger.level <= logging.TRACE:
                logger.trace(log_string, my_name)
            self._children.append(my_name)
            # Decide what to do based on the data_type attribute
            my_data_type = child.get("data_type")
            if my_data_type == "structure":
                child_hli = IDSStructure(self, child)
                setattr(self, my_name, child_hli)
            elif my_data_type == "struct_array":
                from imaspy.ids_struct_array import IDSStructArray

                child_hli = IDSStructArray(self, child)
                setattr(self, my_name, child_hli)
            else:
                # If it is not a structure or struct_array, it is probably a
                # leaf node. Just naively try to generate one
                setattr(
                    self,
                    my_name,
                    create_leaf_container(
                        parent=self,
                        structure_xml=child,
                        var_type=child.get("type"),
                    ),
                )
        # After initialization, always try to convert setting attributes on this structure
        self._convert_ids_types = True

    @property
    def _dd_parent(self) -> IDSMixin:
        if self.metadata.data_type is IDSDataType.STRUCT_ARRAY:
            return self._parent._parent
        return self._parent

    @property
    def has_value(self):
        """True if any of the children has a non-default value"""
        return any(map(lambda el: el.has_value, self))

    def keys(self):
        """Behave like a dictionary by defining a keys() method"""
        return self._children

    def values(self):
        """Behave like a dictionary by defining a values() method"""
        return map(self.__getitem__, self._children)

    def items(self):
        """Behave like a dictionary by defining an items() method"""
        # define values inline, because some IDSes overwrite values
        return zip(self.keys(), map(self.__getitem__, self._children))

    def __iter__(self):
        """Iterate over this structure's children"""
        return iter(map(self.__getitem__, self._children))

    @cached_property
    def depth(self):
        """Calculate the depth of the leaf node"""
        my_depth = 0
        if hasattr(self, "_parent"):
            my_depth += 1 + self._parent.depth
        return my_depth

    def __str__(self):
        return '%s("%s")' % (type(self).__name__, self.metadata.name)

    def __getitem__(self, key):
        keyname = str(key)
        return getattr(self, keyname)

    def __setitem__(self, key, value):
        keyname = str(key)
        self.__setattr__(keyname, value)

    def __setattr__(self, key, value):
        """
        'Smart' setting of attributes. To be able to warn the user on imaspy
        IDS interaction time, instead of on database put time
        Only try to cast user-facing attributes, as core developers might
        want to always bypass this mechanism (I know I do!)
        """
        # TODO: Check if this heuristic is sufficient
        if self._convert_ids_types and not key[0] == "_":
            # Convert IDS type on set time. Never try this for hidden attributes!
            if hasattr(self, key):
                attr = getattr(self, key)
            else:
                # Structure does not exist. It should have been pre-generated
                raise NotImplementedError(
                    "generating new structure from scratch {name}".format(name=key)
                )

                # attr = create_leaf_container(key, no_data_type_I_guess, parent=self)
            if isinstance(attr, IDSStructure) and not isinstance(value, IDSStructure):
                raise TypeError(
                    "Trying to set structure field {!s} with non-structure.".format(key)
                )

            attr.value = value
            # super().__setattr__(key, attr)
        else:
            super().__setattr__(key, value)

    def _validate(self, aos_indices: Dict[str, int]) -> None:
        # Common validation logic
        super()._validate(aos_indices)
        # IDSStructure specific: validate child nodes
        for child in self:
            child._validate(aos_indices)
