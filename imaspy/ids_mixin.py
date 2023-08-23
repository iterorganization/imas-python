# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

import copy
import logging
from typing import Dict
from xml.etree.ElementTree import Element

import scipy.interpolate
from imaspy.ids_data_type import IDSDataType

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from imaspy.exception import ValidationError
from imaspy.ids_metadata import IDSMetadata
from imaspy.setup_logging import root_logger as logger

try:
    from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS, IDS_TIME_MODE_INDEPENDENT
except ImportError as ee:
    logger.critical("IMAS could not be imported. UAL not available! %s", ee)

logger.setLevel(logging.INFO)


class IDSMixin:
    """The base class which unifies properties of structure, struct_array, toplevel, root
    and primitive nodes (IDSPrimitive and IDSNumericArray)"""

    def __init__(self, parent: "IDSMixin", structure_xml: Element):
        """Setup basic properties for a tree node (leaf or non-leaf) such as
        name, _parent, _backend_name etc."""
        self._parent = parent
        self._structure_xml = structure_xml
        self.metadata = IDSMetadata(structure_xml=self._structure_xml)

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
            - `ids.ids_properties.creation_data` is `ids_properties/creation_date`
            - `gyrokinetics.wavevector[0].radial_component_norm` is `wavevector[0]/radial_component_norm
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

    def visit_children(self, fun, leaf_only=False):
        """walk all children of this structure in order and execute fun on them"""
        # you will have fun
        if hasattr(self, "__iter__"):
            if not leaf_only:
                fun(self)
            for child in self:
                child.visit_children(fun, leaf_only)
        else:  # it must be a child then?
            fun(self)

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
        and thus have a common string to start with. We collect that common logic here

        Examples:
            - `gyrokinetics.wavevector[0].eigenmode[0].time_norm` is
                `<IDSNumericArray (IDS:gyrokinetics, wavevector[0]/eigenmode[0]/time_norm`
            - `wavevector[0].eigenmode[0].frequency_norm` is
                `<IDSPrimitive (IDS:gyrokinetics, wavevector[0]/eigenmode[0]/frequency_norm`
        """
        my_repr = f"<{type(self).__name__}"
        my_repr += f" (IDS:{self._toplevel.metadata.name},"
        my_repr += f" {self._path}"
        return my_repr

    def resample(
        self, old_time, new_time, homogeneousTime=None, inplace=False, **kwargs
    ):
        """Resample all primitives in their time dimension to a new time array"""
        if "ids_properties" in self and homogeneousTime is None:
            homogeneousTime = self.ids_properties.homogeneous_time

        if homogeneousTime is None:
            raise ValueError(
                "homogeneous_time is not specified in ids_properties nor given"
                " as keyword argument"
            )

        if homogeneousTime != IDS_TIME_MODE_HOMOGENEOUS:
            # TODO: implement also for IDS_TIME_MODE_INDEPENDENT
            # (and what about converting between time modes? this gets tricky fast)
            raise NotImplementedError(
                "resample is only implemented for IDS_TIME_MODE_HOMOGENEOUS"
            )

        # we need to import here to avoid circular dependencies
        from imaspy.ids_toplevel import IDSToplevel

        def visitor(el):
            if not el.has_value:
                return
            if (
                getattr(el, "_var_type", None) == "dynamic"
                and el.metadata.name != "time"
            ):
                # effectively a guard to get only idsPrimitive
                # TODO: also support time axes as dimension of IDSStructArray
                if el.time_axis is None:
                    logger.warning(
                        "No time axis found for dynamic structure %s", self._path
                    )
                interpolator = scipy.interpolate.interp1d(
                    old_time.value, el.value, axis=el.time_axis, **kwargs
                )
                el.value = interpolator(new_time)

        if not inplace:
            el = copy.deepcopy(self)
        else:
            el = self

        el.visit_children(visitor)

        if isinstance(el, IDSToplevel):
            el.time = new_time
        else:
            logger.warning(
                "Performing resampling on non-toplevel. "
                "Be careful to adjust your time base manually"
            )

        return el

    @cached_property
    def time_axis(self):
        """Return the time axis for this node (None if no time dependence)"""
        return self.coordinates.time_index

    @cached_property
    def _toplevel(self) -> "IDSToplevel":
        """Return the toplevel instance this node belongs to"""
        return self._parent._toplevel

    def _validate(self, aos_indices: Dict[str, int]) -> None:
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
                    "mode is IDS_TIME_MODE_INDEPENDENT.",
                    aos_indices,
                )
