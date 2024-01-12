# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""A structure in an IDS
"""

import logging
from copy import deepcopy
from functools import lru_cache
from typing import Generator, List

from xxhash import xxh3_64

from imaspy.al_context import LazyALContext
from imaspy.ids_metadata import IDSDataType, IDSMetadata
from imaspy.ids_base import IDSBase
from imaspy.ids_path import IDSPath
from imaspy.ids_primitive import (
    IDSComplex0D,
    IDSFloat0D,
    IDSInt0D,
    IDSNumericArray,
    IDSPrimitive,
    IDSString0D,
    IDSString1D,
)
from imaspy.ids_struct_array import IDSStructArray

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def get_node_type(data_type: IDSDataType, ndim: int):
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


class IDSStructure(IDSBase):
    """IDS structure node

    Represents a node in the IDS tree. Does not itself contain data,
    but contains references to leaf nodes with data (IDSPrimitive) or
    other node-like structures, for example other IDSStructures or
    IDSStructArrays
    """

    def __init__(self, parent: IDSBase, metadata: IDSMetadata):
        """Initialize IDSStructure from XML specification

        Initializes in-memory an IDSStructure. The XML should contain
        all direct descendants of the node. To avoid duplication,
        none of the XML structure is saved directly, so this transformation
        might be irreversible.

        Args:
            parent: Parent structure. Can be anything, but at database write
                time should be something with a path attribute
            metadata: IDSMetadata describing the structure of the IDS
        """
        # Performance hack: bypass our __setattr__ implementation during __init__:
        orig_setattr = IDSStructure.__setattr__
        del IDSStructure.__setattr__
        try:
            super().__init__(parent, metadata)
            self._children = self.metadata._children
            self._lazy_context = None
        finally:
            IDSStructure.__setattr__ = orig_setattr

    def __getattr__(self, name):
        if name not in self._children:
            raise AttributeError(f"'{self.__class__}' object has no attribute '{name}'")
        # Create child node
        child_meta = self._children[name]
        child = get_node_type(child_meta.data_type, child_meta.ndim)(self, child_meta)
        super().__setattr__(name, child)  # bypass setattr logic below: avoid recursion
        if self._lazy:  # lazy load the child
            from imaspy.db_entry_helpers import _get_child

            _get_child(child, self._lazy_context)
        return child

    def __setattr__(self, key, value):
        """
        'Smart' setting of attributes. To be able to warn the user on imaspy
        IDS interaction time, instead of on database put time
        Only try to cast user-facing attributes, as core developers might
        want to always bypass this mechanism (I know I do!)
        """
        # Skip logic for any value that is not a child IDS node
        if key.startswith("_") or key not in self._children:
            return super().__setattr__(key, value)

        # This will raise an attribute error when there is no child named 'key', fine?
        attr = getattr(self, key)

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

    def __deepcopy__(self, memo):
        if self._lazy:
            raise NotImplementedError(
                "deepcopy is not implemented for lazy-loaded IDSs."
            )
        copy = self.__class__(self._parent, self.metadata)
        for child in self._children:
            if child in self.__dict__:
                child_copy = deepcopy(getattr(self, child), memo)
                setattr(copy, child, child_copy)
        return copy

    def __dir__(self) -> List[str]:
        return sorted(set(object.__dir__(self)).union(self._children))

    def _set_lazy_context(self, ctx: LazyALContext) -> None:
        """Called by DBEntry during a lazy get/get_slice.

        Set the context that we can use for retrieving our children.
        """
        self._lazy_context = ctx

    @property
    def _dd_parent(self) -> IDSBase:
        if self.metadata.data_type is IDSDataType.STRUCT_ARRAY:
            return self._parent._parent
        return self._parent

    @property
    def has_value(self) -> bool:
        """True if any of the children has a non-default value"""
        if self._lazy:
            raise NotImplementedError(
                "`has_value` is not implemented for lazy-loaded structures."
            )
        for _ in self.iter_nonempty_():
            return True
        return False

    def iter_nonempty_(self, *, accept_lazy=False) -> Generator[IDSBase, None, None]:
        """Iterate over all child nodes with non-default value.

        Note:
            The name ends with an underscore so it won't clash with IDS child names.

        Caution:
            This method works differently for lazy-loaded IDSs.

            By default, an error is raised when calling this method for lazy loaded
            IDSs. You may set the keyword argument ``accept_lazy`` to ``True`` to
            iterate over all `loaded` child nodes with a non-default value. See below
            example for lazy-loaded IDSs.

        Examples:

            .. code-block:: python
                :caption: ``iter_nonempty_`` for fully loaded IDSs

                >>> import imaspy.training
                >>> entry = imaspy.training.get_training_db_entry()
                >>> cp = entry.get("core_profiles")
                >>> list(cp.iter_nonempty_())
                [
                    <IDSStructure (IDS:core_profiles, ids_properties)>,
                    <IDSStructArray (IDS:core_profiles, profiles_1d with 3 items)>,
                    <IDSNumericArray (IDS:core_profiles, time, FLT_1D)>
                    numpy.ndarray([  3.98722186, 432.93759781, 792.        ])
                ]

            .. code-block:: python
                :caption: ``iter_nonempty_`` for lazy-loaded IDSs

                >>> import imaspy.training
                >>> entry = imaspy.training.get_training_db_entry()
                >>> cp = entry.get("core_profiles", lazy=True)
                >>> list(cp.iter_nonempty_())
                RuntimeError: Iterating over non-empty nodes of a lazy loaded IDS will
                skip nodes that are not loaded. Set accept_lazy=True to continue.
                See the documentation for more information: [...]
                >>> list(cp.iter_nonempty_(accept_lazy=True))
                []
                >>> # An empty list because nothing is loaded. Load `time`:
                >>> cp.time
                <IDSNumericArray (IDS:core_profiles, time, FLT_1D)>
                numpy.ndarray([  3.98722186, 432.93759781, 792.        ])
                >>> list(cp.iter_nonempty_(accept_lazy=True))
                [<IDSNumericArray (IDS:core_profiles, time, FLT_1D)>
                numpy.ndarray([  3.98722186, 432.93759781, 792.        ])]

        Keyword Args:
            accept_lazy: Accept that this method will only yield loaded nodes of a
                lazy-loaded IDS. Non-empty nodes that have not been loaded from the
                backend are not iterated over. See detailed explanation above.
        """
        if self._lazy and not accept_lazy:
            raise RuntimeError(
                "Iterating over non-empty nodes of a lazy loaded IDS will skip nodes "
                "that are not loaded. Set accept_lazy=True to continue. "
                "See the documentation for more information: "
                "https://sharepoint.iter.org/departments/POP/CM/IMDesign/"
                "Code%20Documentation/IMASPy-doc/generated/imaspy.ids_structure."
                "IDSStructure.html#imaspy.ids_structure.IDSStructure.iter_nonempty_"
            )
        for child in self._children:
            if child in self.__dict__:
                child_node = getattr(self, child)
                if (  # IDSStructure.has_value is not implemented when lazy-loaded:
                    self._lazy and isinstance(child_node, IDSStructure)
                ) or child_node.has_value:
                    yield child_node

    def __iter__(self):
        """Iterate over this structure's children"""
        return iter(map(self.__getitem__, self._children))

    def __str__(self):
        return '%s("%s")' % (type(self).__name__, self.metadata.name)

    def __getitem__(self, key):
        keyname = str(key)
        if keyname in self._children:
            return getattr(self, keyname)

        path = IDSPath(keyname)
        if len(path) == 1 and path.indices[0] is None:
            raise AttributeError(f"'{self!r}' has no attribute '{keyname}'")

        return path.goto(self, from_root=False)

    def __repr__(self):
        return f"{self._build_repr_start()})>"

    def __setitem__(self, key, value):
        keyname = str(key)
        if keyname in self._children:
            return self.__setattr__(keyname, value)

        path = IDSPath(keyname)
        if len(path) == 1 and path.indices[0] is None:
            raise AttributeError(f"'{self!r}' has no attribute '{keyname}'")

        attr = path.goto(self, from_root=False)
        if isinstance(attr, IDSPrimitive):
            attr.value = value
        else:
            # Setting an IDSStructArray or IDSStructure: delegate to the
            # relevant __setitem__ of its parent
            parent = attr._parent
            parent[path.parts[-1]] = value

    def _validate(self) -> None:
        # Common validation logic
        super()._validate()
        # IDSStructure specific: validate child nodes
        # accept_lazy=True: users are warned in IDSToplevel.validate()
        for child in self.iter_nonempty_(accept_lazy=True):
            child._validate()

    def _xxhash(self) -> bytes:
        hsh = xxh3_64()
        children = sorted(self._children)

        # Skip ids_properties.version_put
        if self.metadata.name == "ids_properties":
            if "version_put" in children:  # Some old DDs don't have version_put defined
                children.remove("version_put")

        for childname in children:
            child = self[childname]
            if not child.has_value:
                continue

            hsh.update(childname.encode("UTF-8"))
            hsh.update(child._xxhash())

        return hsh.digest()
