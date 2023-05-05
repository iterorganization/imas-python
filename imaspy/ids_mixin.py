# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.

import copy
import logging
from xml.etree.ElementTree import Element

from packaging.version import Version as V
import scipy.interpolate

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from imaspy.al_exception import ALException
from imaspy.context_store import context_store
from imaspy.ids_metadata import IDSMetadata
from imaspy.setup_logging import root_logger as logger

try:
    from imaspy.ids_defs import IDS_TIME_MODE_HETEROGENEOUS, IDS_TIME_MODE_HOMOGENEOUS
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

        self._last_backend_xml_hash = None
        self._backend_name = None

    def getRelCTXPath(self, ctx: int) -> str:
        """Get the path relative to given context from an absolute path"""
        return context_store.strip_context(self._path, ctx)

    def getTimeBasePath(self, homogeneousTime, ignore_nbc_change=1):
        if any(coordinate.is_time_coordinate for coordinate in self.metadata.coordinates):
            if homogeneousTime == IDS_TIME_MODE_HOMOGENEOUS:
                return "/time"
            if homogeneousTime == IDS_TIME_MODE_HETEROGENEOUS:
                # TODO: this probably doesn't work, but heterogeneous time mode is not
                # tested at all...
                return self.getAOSPath(ignore_nbc_change) + "/time"
            raise ALException(
                "Unexpected call to function getTimeBasePath(cls, homogeneousTime) "
                f"with undefined homogeneous time. {homogeneousTime}"
            )
        if self.metadata.name == "time" and self.depth == 1:
            return "/time"
        return ""

    def getAOSPath(self, ignore_nbc_change=1):
        # TODO: Fix in case it gives trouble
        # This is probably wrong! Should walk up the tree
        return self._backend_name or self.metadata.name

    @cached_property
    def _path(self):
        """Build absolute path from node to root _in backend coordinates_"""
        my_path = self._backend_name or self.metadata.name
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

    @cached_property
    def _ull(self):
        try:
            return self._parent._ull
        except AttributeError as ee:
            raise RuntimeError("ULL directly connected to %s", self) from ee

    def __getstate__(self):
        """Override getstate so _ull is not passed along. Otherwise we have
        problems deepcopying elements"""

        state = self.__dict__.copy()
        try:
            del state["_ull"]
        except KeyError:
            pass
        return state

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

    @cached_property
    def backend_version(self):
        """Return the data dictionary version of the backend structure."""
        if hasattr(self, "_parent"):
            return self._parent.backend_version

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

    def set_backend_properties(self, structure_xml):
        """Walk existing children to match those in structure_xml, then
        set backend annotations for this element and its children.

        Returns up, skip.
        - up: True if memory version is newer than backend version, otherwise False
        - skip: True if the _last_backend_xml_hash == hash of structure_xml
          this implies we don't need to reset the backend properties
          of all children, only their path

        """

        # Only do this once per structure_xml so repeated calls are not expensive
        if self._last_backend_xml_hash == hash(structure_xml):
            # We need to delete the self._path cache on all children of this one
            # without duplicating the work maybe.
            # only walk all children when the rest of the work is skipped, otherwise
            # the recursiveness of set_backend_properties solves it
            self.reset_path()
            self.visit_children(IDSMixin.reset_path)
            return None, False
        self._last_backend_xml_hash = hash(structure_xml)

        # temporarily save the xml tree here (it is deleted later)
        self._backend_structure_xml = structure_xml

        self.reset_path()
        if "backend_version" in self.__dict__:
            del self.__dict__["backend_version"]  # Delete the cached_property cache
            # this is how it works for functools cached_property.
            # how is it for cached_property package?

        up = self._version and V(self._version) > V(
            self.backend_version or self._version
        )  # True if backend older than frontend
        # if they were the same we shouldn't be here
        # if self.backend_version is undefined we are loading raw xml files
        # TODO: get the version number from the file in that case
        # for now just assume it's a down migration.

        self._backend_name = structure_xml.attrib["name"]

        return up, False
