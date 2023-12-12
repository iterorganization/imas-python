# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

import logging
from typing import TYPE_CHECKING

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from imaspy.exception import ValidationError
from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT
from imaspy.ids_metadata import IDSMetadata

if TYPE_CHECKING:
    from imaspy.ids_toplevel import IDSToplevel

logger = logging.getLogger(__name__)


class IDSMixin:
    """The base class which unifies properties of structure, struct_array, toplevel
    and primitive nodes (IDSPrimitive and IDSNumericArray)."""

    def __init__(self, parent: "IDSMixin", metadata: IDSMetadata):
        """Setup basic properties for a tree node (leaf or non-leaf) such as
        name, _parent, _backend_name etc."""
        self._parent = parent
        self.metadata = metadata
        dd_doc = getattr(self.metadata, "documentation", None)
        if dd_doc:
            self.__doc__ = dd_doc

    @property
    def _time_mode(self) -> int:
        """Retrieve the time mode from `/ids_properties/homogeneous_time`"""
        return self._parent._time_mode

    @property
    def _dd_parent(self) -> "IDSMixin":
        """Return the DD parent element

        Usually this is the same as the _parent element, but for IDSStructArray
        structure sub-elements, this will return the parent of the IDSStructArray.

        Examples:
            - `ids.ids_properties.provenance._dd_parent` is `ids.ids_properties`
            - `ids.ids_properties.provenance[0]._dd_parent` is also `ids.ids_properties`
        """
        return self._parent

    @cached_property
    def _is_dynamic(self) -> bool:
        """True if this element (or any parent) has type=dynamic"""
        return self.metadata.type.is_dynamic or self._dd_parent._is_dynamic

    @property
    def _path(self) -> str:
        """Build relative path from the toplevel to the node

        Examples:
            - ``ids.ids_properties.creation_data._path`` is
              ``"ids_properties/creation_date"``
            - ``gyrokinetics.wavevector[0].radial_component_norm._path`` is
              ``"wavevector[0]/radial_component_norm"``
        """
        from imaspy.ids_struct_array import IDSStructArray

        parent_path = self._parent._path
        my_path = self.metadata.name
        if isinstance(self._parent, IDSStructArray):
            if self in self._parent.value:
                index = self._parent.value.index(self)
            else:
                # This happens when we ask the path of a struct_array
                # child that does not have a proper parent anymore
                # E.g. a resize
                logger.warning(
                    "Link to parent of %s broken. Cannot reconstruct index", my_path
                )
                index = "?"
            my_path = f"{parent_path}[{index}]"
        elif parent_path != "":
            # If we are not an IDSStructArray, we have no indexable children.
            my_path = parent_path + "/" + my_path
        return my_path

    @cached_property
    def _lazy(self):
        """Whether this IDSMixin is part of a lazy-loaded IDSToplevel"""
        return self._parent._lazy

    @cached_property
    def _version(self):
        """Return the data dictionary version of this in-memory structure."""
        # As each Mixin (e.g. "data node") should have a parent, we just have to
        # check its parent.
        if hasattr(self, "_parent"):
            return self._parent._version

    def _build_repr_start(self) -> str:
        """Build the start of the string derived classes need for their repr.

        All derived classes need to represent the IDS they are part of,
        and thus have a common string to start with. We collect that common logic here.
        """
        my_repr = f"<{type(self).__name__}"
        my_repr += f" (IDS:{self._toplevel.metadata.name},"
        my_repr += f" {self._path}"
        return my_repr

    @cached_property
    def _toplevel(self) -> "IDSToplevel":
        """Return the toplevel instance this node belongs to"""
        return self._parent._toplevel

    def _validate(self) -> None:
        """Actual implementation of validation logic.

        See also:
            :py:meth:`imaspy.ids_toplevel.IDSToplevel.validate`.

        Args:
            aos_indices: index_name -> index, e.g. {"i1": 1, "itime": 0}, for all parent
                array of structures.
        """
        if self.metadata.type.is_dynamic and self.has_value:
            if self._time_mode == IDS_TIME_MODE_INDEPENDENT:
                raise ValidationError(
                    f"Dynamic variable {self.metadata.path} is allocated, but time "
                    "mode is IDS_TIME_MODE_INDEPENDENT."
                )
