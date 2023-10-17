# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" A structure in an IDS

* :py:class:`IDSStructure`
"""

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from copy import deepcopy
from functools import lru_cache
import logging
from xml.etree.ElementTree import Element

from imaspy.ids_metadata import IDSDataType
from imaspy.ids_mixin import IDSMixin
from imaspy.ids_primitive import (
    IDSComplex0D,
    IDSFloat0D,
    IDSInt0D,
    IDSNumericArray,
    IDSString1D,
    IDSString0D,
)
from imaspy.ids_struct_array import IDSStructArray

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def get_node_type(data_type: str):
    data_type, ndim = IDSDataType.parse(data_type)
    if data_type is IDSDataType.STRUCTURE:
        return IDSStructure
    if data_type is IDSDataType.STRUCT_ARRAY:
        return IDSStructArray
    if data_type is IDSDataType.STR:
        if ndim == 0:
            return IDSString0D
        else:
            return IDSString1D
    if ndim == 0:
        if data_type is IDSDataType.FLT:
            return IDSFloat0D
        if data_type is IDSDataType.INT:
            return IDSInt0D
        if data_type is IDSDataType.CPX:
            return IDSComplex0D
    return IDSNumericArray


class IDSStructure(IDSMixin):
    """IDS structure node

    Represents a node in the IDS tree. Does not itself contain data,
    but contains references to leaf nodes with data (IDSPrimitive) or
    other node-like structures, for example other IDSStructures or
    IDSStructArrays
    """

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
        super().__init__(parent, structure_xml=structure_xml)

        self._children = []  # Store the children as a list of strings.
        # Loop over the direct descendants of the current node.
        # Do not loop over grandchildren, that is handled by recursiveness.

        for child in structure_xml:
            my_name = child.get("name")
            self._children.append(my_name)
            child_node = get_node_type(child.get("data_type"))(self, child)
            setattr(self, my_name, child_node)
        # After initialization, always try to convert setting attributes on this structure
        self._convert_ids_types = True

    def __deepcopy__(self, memo):
        copy = self.__class__(self._parent, self._structure_xml)
        for child in self._children:
            child_copy = deepcopy(getattr(self, child))
            setattr(copy, child, child_copy)
        return copy

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

    def __str__(self):
        return '%s("%s")' % (type(self).__name__, self.metadata.name)

    def __getitem__(self, key):
        keyname = str(key)
        return getattr(self, keyname)

    def __repr__(self):
        return f"{self._build_repr_start()})>"

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

            if isinstance(attr, IDSStructure):
                if not isinstance(value, IDSStructure):
                    raise TypeError(
                        f"Trying to set structure field {key} with non-structure."
                    )
                if value.metadata.path != attr.metadata.path:
                    raise ValueError(
                        f"Trying to set structure field {attr.metadata.path} "
                        f"with a non-matching structure {value.metadata.path}."
                    )
                super().__setattr__(key, value)
                value._parent = self
            elif isinstance(attr, IDSStructArray):
                if not isinstance(value, IDSStructArray):
                    raise TypeError(
                        f"Trying to set struct array field {key} with non-struct-array."
                    )
                if value.metadata.path != attr.metadata.path:
                    raise ValueError(
                        f"Trying to set struct array field {attr.metadata.path} "
                        f"with a non-matching struct array {value.metadata.path}."
                    )
                super().__setattr__(key, value)
                value._parent = self
            else:
                attr.value = value
        else:
            super().__setattr__(key, value)

    def _validate(self) -> None:
        # Common validation logic
        super()._validate()
        # IDSStructure specific: validate child nodes
        for child in self:
            child._validate()
