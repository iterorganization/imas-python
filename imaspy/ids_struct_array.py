# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" IDS StructArray represents an Array of Structures in the IDS tree.
This contains references to :py:class:`IDSStructure`s

* :py:class:`IDSStructArray`
"""

from copy import deepcopy
from typing import Optional, Tuple
from xml.etree.ElementTree import Element

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from imaspy.al_context import LazyALContext
from imaspy.ids_coordinates import IDSCoordinates
from imaspy.ids_mixin import IDSMixin
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

        # Initialize with an 0-length list
        self.value = []

        # Lazy loading context, only applicable when self._lazy is True
        # When lazy loading, all items in self.value are None until they are requested
        self._lazy_loaded = False  # Marks if we already loaded our size
        self._lazy_context: Optional[LazyALContext] = None
        self._lazy_paths = ("", "")  # path, timebasepath

    @cached_property
    def coordinates(self):
        return IDSCoordinates(self)

    def __deepcopy__(self, memo):
        copy = self.__class__(self._parent, self._structure_xml)
        for value in self.value:
            value_copy = deepcopy(value, memo)
            value_copy._parent = copy
            copy.value.append(value_copy)
        return copy

    def _set_lazy_context(self, ctx: LazyALContext, path: str, timebase: str) -> None:
        """Called by DBEntry during a lazy get/get_slice.

        Set the context that we can use for retrieving our size and children.
        """
        self._lazy_context = ctx
        self._lazy_paths = (path, timebase)

    def _load(self, item: Optional[int]) -> None:
        """When lazy loading, ensure that the requested item is loaded.

        Args:
            item: index of the item to load. When None, just ensure that our size is
                loaded from the lowlevel.
        """
        assert self._lazy
        assert self._lazy_context
        if self._lazy_loaded:
            if item is None:
                return
            if self.value[item] is not None:
                return  # item is already loaded
        # Load requested data from the backend
        manager = self._lazy_context.lazy_arraystruct_action(*self._lazy_paths, item)
        with manager as (new_ctx, size):
            # Note: we can be a bit more efficient here by recognizing that the returned
            # LazyALContext (new_ctx) for different items is essentially the same,
            # except for the requested item number. It would need some work to get
            # right, so keep the logic like this unless we find it to be a bottleneck.
            if not self._lazy_loaded:
                self.value = [None] * size
                self._lazy_loaded = True
            assert len(self.value) == size

            if item is not None:
                # Create and (lazily) load the requested item
                from imaspy.db_entry import _get_children
                from imaspy.ids_structure import IDSStructure

                element = self.value[item] = IDSStructure(self, self._structure_xml)
                nbc_map = self._lazy_context.nbc_map
                _get_children(element, new_ctx, self._time_mode, "", nbc_map)

    @property
    def _element_structure(self):
        """Prepare an element structure JIT"""
        from imaspy.ids_structure import IDSStructure

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
        if self._lazy:
            self._load(item)
        return self.value[list_idx]

    def __setitem__(self, item, value):
        # value is a list, so the given item should be convertable to integer
        # TODO: perhaps we should allow slices as well?
        if self._lazy:
            raise ValueError("Lazy-loaded IDSs are read-only.")
        list_idx = int(item)
        self.value[list_idx] = value

    def __len__(self) -> int:
        if self._lazy:
            self._load(None)
        return len(self.value)

    @property
    def shape(self) -> Tuple[int]:
        if self._lazy:
            self._load(None)
        return (len(self.value),)

    def append(self, elt):
        """Append elements to the end of the array of structures.

        Parameters
        ----------
        """
        if self._lazy:
            raise ValueError("Lazy-loaded IDSs are read-only.")
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
            e._parent = self
            self.value.append(e)

    def __repr__(self):
        return f"{self._build_repr_start()} with {len(self)} items)>"

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
        if self._lazy:
            raise ValueError("Lazy-loaded IDSs are read-only.")
        if nbelt < 0:
            raise ValueError(f"Invalid size {nbelt}: size may not be negative")
        if not keep:
            self.value = []
        cur = len(self.value)
        if nbelt > cur:
            new_els = []
            for _ in range(nbelt - cur):
                new_el = self._element_structure
                new_els.append(new_el)
            self.append(new_els)
        elif nbelt < cur:
            self.value = self.value[:nbelt]
        else:  # nbelt == cur
            pass  # nothing to do, already correct size

    @property
    def has_value(self) -> bool:
        """True if this struct-array has nonzero size"""
        # Note self.__len__ will lazy load our size if needed
        return len(self) > 0

    def _validate(self) -> None:
        # Common validation logic
        super()._validate()
        # IDSStructArray specific: validate coordinates and child nodes
        if self.has_value:
            self.coordinates._validate()
            for child in self:
                child._validate()
