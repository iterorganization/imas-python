# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

import copy
import logging
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
        """True iff this element has type=dynamic, or it has a parent with type=dynamic
        """
        return self.metadata.type.is_dynamic or self._dd_parent._is_dynamic

    @cached_property
    def _path(self):
        """Build absolute path from node to root _in backend coordinates_"""
        my_path = self.metadata.name
        if hasattr(self, "_parent"):
            # these exceptions may be slow. (But cached, so not so bad?)
            try:
                if self._parent._array_type:
                    try:
                        my_path = "{!s}/{!s}".format(
                            self._parent._path, self._parent.value.index(self) + 1
                        )
                    except ValueError as e:
                        # this happens when we ask the path of a struct_array child
                        # which is 'in waiting'. It is not in its parents value
                        # list yet, so we are here. There is no proper path to mention.
                        # instead we use the special index :
                        my_path = "{!s}/:".format(self._parent._path)
                        raise NotImplementedError(
                            "Paths of unlinked struct array children are not implemented"
                        ) from e
                else:
                    my_path = self._parent._path + "/" + my_path
            except AttributeError:
                my_path = self._parent._path + "/" + my_path
        return my_path

    def reset_path(self):
        if "_path" in self.__dict__:
            del self.__dict__["_path"]  # Delete the cached_property cache
            # this is how it works for functools cached_property.
            # how is it for cached_property package?

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
        if hasattr(self, "_parent"):
            return self._parent._version

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

    def _validate(self) -> None:
        """Actual implementation of validation logic.

        See also:
            :py:meth:`imaspy.ids_toplevel.IDSToplevel.validate`.
        """
        if self.metadata.type.is_dynamic and self.has_value:
            if self._time_mode == IDS_TIME_MODE_INDEPENDENT:
                raise ValidationError(
                    f"Dynamic variable {self.metadata.path} is allocated, but time "
                    "mode is IDS_TIME_MODE_INDEPENDENT."
                )

        # Coordinate validation, but only for 1D+ types that are not empty
        if hasattr(self, "coordinates") and self.has_value:
            self.coordinates._validate()

        # Recurse into children
        if self.metadata.data_type in (
            None,  # IDSToplevel
            IDSDataType.STRUCTURE,
            IDSDataType.STRUCT_ARRAY,
        ):
            for child in self:
                child._validate()
