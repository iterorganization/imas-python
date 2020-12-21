# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.

import logging

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

logger.setLevel(logging.WARNING)


class IDSMixin:
    def getRelCTXPath(self, ctx):
        """ Get the path relative to given context from an absolute path"""
        # This could be replaced with the fullPath() method provided by the LL-UAL
        if self.path.startswith(context_store[ctx]):
            # If the given path indeed starts with the context path. This should
            # always be the case. Grab the part of the path _after_ the context
            # path string
            if context_store[ctx] == "/":
                # The root context is special, it does not have a slash before
                rel_path = self.path[len(context_store[ctx]) :]
            else:
                rel_path = self.path[len(context_store[ctx]) + 1 :]
            split = rel_path.split("/")
            try:
                # Check if the first part of the path is a number. If it is,
                # strip it, it is implied by context
                int(split[0])
            except (ValueError):
                pass
            else:
                # Starts with numeric, strip. Is captured in context
                # TODO: Might need to be recursive.
                rel_path = "/".join(split[1:])
        else:
            from IPython import embed

            embed()
            raise Exception(
                "Could not strip context from absolute path {!s}, store: {!s}".format(
                    self.path, context_store
                )
            )
        # logger.debug('Got context {!s} with abspath {!s}, relpath is {!s}'
        # .format(ctx, self.path, rel_path))
        return rel_path

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
        """Build absolute path from node to root"""
        my_path = self._name
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

    @property
    def _ull(self):
        if not hasattr(self, "_parent"):
            raise Exception("ULL directly connected to {!s}".format(self))
        return self._parent._ull
