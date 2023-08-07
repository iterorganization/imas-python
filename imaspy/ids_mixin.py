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
    def _path(self):
        # Test if we are a part of a tree
        my_path = self._relative_path
        # We have a parent, but do we have a sane toplevel?
        try:
            top = self._toplevel
        except AttributeError as e:
            # We cannot find a toplevel. Just assume whatever we have found
            # with _relative_path is our full path without IDS
            return my_path.lstrip("/")
            # TODO: Check if we want to support this case, otherwise return next Erro
            # raise NotImplementedError(
            #     f"No valid toplevel found for '{my_path}'. Cannot reconstruct path"
            # ) from e
        else:
            # You have a sane toplevel, so you can strip it
            return my_path[len(top._relative_path) + 1 :]

    @property
    def _relative_path(self):
        """Build relative path from the toplevel to the node"""
        # This includes the toplevel name with a slash at the start
        my_path = self.metadata.name
        if hasattr(self._parent, "value"):
            # All array-like elements have a "value" where we need some
            # specific path handling

            if hasattr(self._parent.value, "index"):
                # For our well-defined IMASPy object, we just need to
                # handle the case where the value is indexable. We assume
                # the parents path can always be determined.
                try:
                    return "{!s}[{!s}]".format(
                        self._parent._relative_path, self._parent.value.index(self)
                    )
                except ValueError as e:
                    # this happens when we ask the path of a struct_array
                    # child that is mangled so much that the parent node of
                    # the parent is no longer indexable. In that case,
                    # raise a sane error
                    my_path = f"{self._parent._relative_path}[?]/{my_path}"
                    raise NotImplementedError(
                        f"Link to parent of {my_path} broken. Cannot reconstruct index"
                    ) from e
        elif hasattr(self._parent, "_relative_path"):
            # If we do not have a "value" attribute, we are for sure not an
            # array, and constructing a path is simple
            return self._parent._relative_path + "/" + my_path
        else:
            # We have a parent, but not a sane path. Return ourselves
            return f"{my_path}"

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
        # As each Mixin (e.g. "data node") should have a parent, we just have to
        # check its parent.
        if hasattr(self, "_parent"):
            return self._parent._version

    def _build_repr_start(self):
        my_repr = f"<{type(self).__name__}"
        my_repr += f" (IDS:{self._toplevel._relative_path},"
        my_repr += f" {self._path}"
        return my_repr

    def __repr__(self):
        my_repr = self._build_repr_start()
        my_repr += f", {self.data_type}"
        my_repr += ")>"

        # Numpy is handled slightly differently, as it needs an extra import
        # Also, printing arrays is quite difficult, as we don't know the length
        # nor preferred formatting per se. As we want to print the full
        # thing that could _theoretically_ reproduce the array, we do
        # some numpy magic here
        potential_numpy_str = repr(self.value)
        # This is either something that has array(), and implies a numpy array
        # or just a number. Check for this, and be careful. This may never fail!
        if potential_numpy_str.startswith("array(") and potential_numpy_str.endswith(
            ")"
        ):
            # This is numpy-array style array. Easy!
            potential_numpy_str = potential_numpy_str[6:-1]
            # We should end up with something list-like, check this
            assert potential_numpy_str.startswith("[")
            potential_numpy_str = f"{potential_numpy_str}"

        # Now append the value repr to our own native repr
        my_repr += f" \n{_fullname(self.value)}({potential_numpy_str})"
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
        """Return the name of the toplevel this node belongs to"""
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


def _fullname(o):
    """Get the full name to a type, including module name etc."""
    class_ = o.__class__
    module = class_.__module__
    if module == "builtins":
        return class_.__qualname__  # avoid outputs like 'builtins.str'
    return module + "." + class_.__qualname__
