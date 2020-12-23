# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.

import logging
from distutils.version import StrictVersion as V

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from imaspy.al_exception import ALException
from imaspy.context_store import context_store
from imaspy.logger import logger

try:
    from imaspy.ids_defs import IDS_TIME_MODE_HETEROGENEOUS, IDS_TIME_MODE_HOMOGENEOUS
except ImportError as ee:
    logger.critical("IMAS could not be imported. UAL not available! %s", ee)

logger.setLevel(logging.INFO)


class IDSMixin:
    def getRelCTXPath(self, ctx):
        """ Get the path relative to given context from an absolute path"""
        # This could be replaced with the fullPath() method provided by the LL-UAL
        if self.path.startswith(context_store[ctx]):
            # strip the context path as well as any numeric indices
            # (those are handled by the context store)
            return self.path[len(context_store[ctx]) :].lstrip("/0123456789")
        else:
            from IPython import embed

            embed()
            raise Exception(
                "Could not strip context from absolute path {!s}, store: {!s}".format(
                    self.path, context_store
                )
            )

    def getTimeBasePath(self, homogeneousTime, ignore_nbc_change=1):
        strTimeBasePath = ""
        # Grab timebasepath from the coordinates.
        # TODO: In some cases the timebasepath is stored in the XML directly.
        #       What has priority in case it conflicts? Regardless, this is not
        #       handled by imaspy atm
        if self._coordinates != {}:
            if (
                self._coordinates["coordinate1"].endswith("time")
                and "coordinate2" not in self._coordinates
            ):
                # Should Walk up the tree
                # Just stupid copy for now
                # strTimeBasePath = self._coordinates['coordinate1']
                try:  # see if we can get a value out of the thing
                    homogeneousTime = homogeneousTime.value
                except AttributeError:
                    pass
                if homogeneousTime == IDS_TIME_MODE_HOMOGENEOUS:
                    strTimeBasePath = "/time"
                elif homogeneousTime == IDS_TIME_MODE_HETEROGENEOUS:
                    strTimeBasePath = self.getAOSPath(ignore_nbc_change) + "/time"
                else:
                    raise ALException(
                        "Unexpected call to function getTimeBasePath(cls, homogeneousTime) \
                        with undefined homogeneous time. {!s}".format(
                            homogeneousTime
                        )
                    )
                pass
            elif (
                self._coordinates["coordinate1"] == "1...N"
                and "coordinate2" not in self._coordinates
            ):
                # If variable only depends on 1...N, no timebasepath
                pass
            else:
                # Stub for explicit handling of other cases
                pass

        return strTimeBasePath

    def getAOSPath(self, ignore_nbc_change=1):
        # TODO: Fix in case it gives trouble
        # This is probably wrong! Should walk up the tree
        return self._name

    @cached_property
    def path(self):
        """Build absolute path from node to root in backend coordinates"""
        my_path = self._backend_name or self._name
        if hasattr(self, "_parent"):
            try:
                if self._parent._array_type:
                    my_path = "{!s}/{!s}".format(
                        self._parent.path, self._parent.value.index(self) + 1
                    )
                else:
                    my_path = self._parent.path + "/" + my_path
            except AttributeError:
                my_path = self._parent.path + "/" + my_path
        return my_path

    def reset_path(self):
        try:
            del self.path
        except AttributeError:  # this happens if self.path has not been cached yet
            pass

    @cached_property
    def _ull(self):
        try:
            return self._parent._ull
        except AttributeError as ee:
            raise Exception("ULL directly connected to %s", self) from ee

    def visit_children(self, fun, leaf_only=False):
        """walk all children of this structure in order and execute fun on them"""
        # you will have fun
        if hasattr(self, "__iter__"):
            for child in self:
                if not leaf_only:
                    fun(child)
                child.visit_children(fun, leaf_only)

    def set_backend_properties(self, structure_xml):
        """Walk existing children to match those in structure_xml, then
        set backend annotations for this element and its children."""

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

        self.reset_path()
        try:
            del self._backend_version  # Delete the cached_property cache
            # if the structure_xml is the same then resetting the _backend_version
            # has no effect, as set_backend_properties will not be called anyway.
        except AttributeError:
            pass

        up = V(self._version) > V(
            self._backend_version
        )  # True if backend older than frontend
        # if they were the same we shouldn't be here

        self._backend_name = structure_xml.attrib["name"]

        return up, False
