# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" IDS StructArray represents an Array of Structures in the IDS tree.
This contains references to :py:class:`IDSStructure`s

* :py:class:`IDSStructArray`
"""

from typing import Dict, Tuple
from xml.etree.ElementTree import Element

from imaspy.ids_coordinates import IDSCoordinates
from imaspy.ids_mixin import IDSMixin
from imaspy.ids_structure import IDSStructure
from imaspy.setup_logging import root_logger as logger


class IDSStructArray(IDSMixin):
    """IDS array of structures (AoS) node

    Represents a node in the IDS tree. Does not itself contain data,
    but contains references to IDSStructures
    """

    # TODO: HLI compatibility
    @staticmethod
    def getAoSElement(self):
        logger.warning(
            "getAoSElement is deprecated, you should never need this", FutureWarning
        )
        return self._element_structure

    # TODO: HLI compatibility `base_path_in`
    def __init__(self, parent: IDSMixin, structure_xml: Element):
        """Initialize IDSStructArray from XML specification

        Args:
            parent: Parent structure. Can be anything, but at database write
                time should be something with a path attribute
            structure_xml: Object describing the structure of the IDS. Usually
                an instance of `xml.etree.ElementTree.Element`
        """
        super().__init__(parent, structure_xml)
        self.coordinates = IDSCoordinates(self)

        self._convert_ids_types = False

        # Initialize with an 0-length list
        self.value = []

        self._convert_ids_types = True

    @property
    def _element_structure(self):
        """Prepare an element structure JIT"""
        struct = IDSStructure(self, self._structure_xml)
        return struct

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def __getattr__(self, key):
        return object.__getattribute__(self, key)

    def __getitem__(self, item):
        # value is a list, so the given item should be convertable to integer
        # TODO: perhaps we should allow slices as well?
        list_idx = int(item)
        return self.value[list_idx]

    def __setitem__(self, item, value):
        # value is a list, so the given item should be convertable to integer
        # TODO: perhaps we should allow slices as well?
        list_idx = int(item)
        if hasattr(self, "_convert_ids_types") and self._convert_ids_types:
            # Convert IDS type on set time. Never try this for hidden attributes!
            if list_idx in self.value:
                struct = self.value[list_idx]
                struct.value = value
        self.value[list_idx] = value

    def __len__(self) -> int:
        return len(self.value)

    def __iter__(self):
        return iter(self.value)

    @property
    def shape(self) -> Tuple[int]:
        return (len(self.value),)

    def append(self, elt):
        """Append elements to the end of the array of structures.

        Parameters
        ----------
        """
        if not isinstance(elt, list):
            elements = [elt]
        else:
            elements = elt
        for e in elements:
            # Just blindly append for now
            # TODO: Maybe check if user is not trying to append weird elements
            if self.metadata.maxoccur and len(self.value) >= self.metadata.maxoccur:
                raise RuntimeError(
                    "Maxoccur is set to %s for %s, not adding %s"
                    % (
                        self.metadata.maxoccur,
                        self.metadata.path,
                        elt,
                    )
                )
            e._convert_ids_types = True
            e._parent = self
            self.value.append(e)

    def __repr__(self):
        my_repr = self._build_repr_start()
        my_repr += f" with {len(self)} items"
        my_repr += ")>"

        return my_repr

    def resize(self, nbelt, keep=False):
        """Resize an array of structures.

        nbelt : int
            The number of elements for the targeted array of structure,
            which can be smaller or bigger than the size of the current
            array if it already exists.
        keep : bool, optional
            Specifies if the targeted array of structure should keep
            existing data in remaining elements after resizing it.
        """
        if nbelt < 0:
            raise ValueError(f"Invalid size {nbelt}: size may not be negative")
        if not keep:
            self.value = []
        cur = len(self.value)
        if nbelt > cur:
            new_els = []
            for _ in range(nbelt - cur):
                new_el = self._element_structure
                new_el._parent = self
                new_el._convert_ids_types = True
                new_els.append(new_el)
            self.append(new_els)
        elif nbelt < cur:
            self.value = self.value[:nbelt]
        else:  # nbelt == cur
            pass  # nothing to do, already correct size

    @property
    def has_value(self) -> bool:
        """True if this struct-array has nonzero size"""
        return len(self.value) > 0

    def _validate(self, aos_indices: Dict[str, int]) -> None:
        # Common validation logic
        super()._validate(aos_indices)
        # IDSStructArray specific: validate coordinates and child nodes
        if not self.has_value:
            return

        self.coordinates._validate(aos_indices)

        # Find out our aos index name
        if "itime" in aos_indices:
            name = f"i{len(aos_indices)}"
        elif self.metadata.type.is_dynamic:
            name = "itime"
        else:
            name = f"i{len(aos_indices)+1}"

        new_indices = aos_indices.copy()
        for i, child in enumerate(self):
            new_indices[name] = i  # Set index of this child
            child._validate(new_indices)
