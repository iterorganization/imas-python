# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" Represents a Top-level IDS (like NBI etc)
* :py:class:`IDSToplevel`
"""

import logging
import os
import re
from typing import TYPE_CHECKING, Optional
import tempfile

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from imaspy.al_exception import ALException
from imaspy.exception import ValidationError
from imaspy.ids_defs import (
    ASCII_BACKEND,
    ASCII_SERIALIZER_PROTOCOL,
    DEFAULT_SERIALIZER_PROTOCOL,
    IDS_TIME_MODE_UNKNOWN,
    IDS_TIME_MODES,
    needs_imas,
)
from imaspy.ids_structure import IDSStructure

if TYPE_CHECKING:
    from imaspy.db_entry import DBEntry
    from imaspy.ids_factory import IDSFactory


logger = logging.getLogger(__name__)


class IDSToplevel(IDSStructure):
    """This is any IDS Structure which has ids_properties as child node

    At minimum, one should fill ids_properties/homogeneous_time
    IF a quantity is filled, the coordinates of that quantity must be filled as well
    """

    def __init__(self, parent: "IDSFactory", structure_xml):
        """Save backend_version and backend_xml and build translation layer.

        Args:
            parent: Parent of ``self``, an instance of :py:class:`IDSFactory`.
            name: Name of this structure. Usually from the ``name`` attribute of
                the IDS toplevel definition.
            structure_xml: XML structure that defines this IDS toplevel.
        """
        super().__init__(parent, structure_xml)

    @property
    def _dd_version(self) -> str:
        return self._version

    @property
    def _time_mode(self) -> int:
        """Retrieve the time mode from `/ids_properties/homogeneous_time`"""
        return self.ids_properties.homogeneous_time

    @property
    def _is_dynamic(self) -> bool:
        return False

    @staticmethod
    def default_serializer_protocol():
        """Return the default serializer protocol."""
        return DEFAULT_SERIALIZER_PROTOCOL

    @needs_imas
    def serialize(self, protocol=None):
        """Serialize this IDS to a data buffer.

        The data buffer can be deserialized from any Access Layer High-Level Interface
        that supports this. Currently known to be: IMASPy, Python, C++ and Fortran.

        Example:

        .. code-block: python

            core_profiles = imaspy.IDSFactory().core_profiles()
            # fill core_profiles with data
            ...

            data = core_profiles.serialize()

            # For example, send `data` to another program with libmuscle.
            # Then deserialize on the receiving side:

            core_profiles = imaspy.IDSFactory().core_profiles()
            core_profiles.deserialize(data)
            # Use core_profiles:
            ...

        Args:
            protocol: Which serialization protocol to use. Currently only
                ASCII_SERIALIZER_PROTOCOL is supported.

        Returns:
            Data buffer that can be deserialized using :meth:`deserialize`.
        """
        if protocol is None:
            protocol = self.default_serializer_protocol()
        if self.ids_properties.homogeneous_time == IDS_TIME_MODE_UNKNOWN:
            raise ALException("IDS is found to be EMPTY (homogeneous_time undefined)")
        if protocol == ASCII_SERIALIZER_PROTOCOL:
            from imaspy.db_entry import DBEntry

            tmpdir = "/dev/shm" if os.path.exists("/dev/shm") else "."
            tmpfile = tempfile.mktemp(prefix="al_serialize_", dir=tmpdir)
            dbentry = DBEntry(ASCII_BACKEND, "serialize", 1, 1, "serialize")
            dbentry.create(options=f"-fullpath {tmpfile}")
            dbentry.put(self)

            try:
                # read contents of tmpfile
                with open(tmpfile, "rb") as f:
                    data = f.read()
            finally:
                os.unlink(tmpfile)  # remove tmpfile from disk
            return bytes([ASCII_SERIALIZER_PROTOCOL]) + data
        raise ValueError(f"Unrecognized serialization protocol: {protocol}")

    @needs_imas
    def deserialize(self, data):
        """Deserialize the data buffer into this IDS.

        See :meth:`serialize` for an example.

        Args:
            data: binary data created by serializing an IDS.
        """
        if len(data) <= 1:
            raise ValueError("No data provided")
        protocol = int(data[0])  # first byte of data contains serialization protocol
        if protocol == ASCII_SERIALIZER_PROTOCOL:
            from imaspy.db_entry import DBEntry

            tmpdir = "/dev/shm" if os.path.exists("/dev/shm") else "."
            tmpfile = tempfile.mktemp(prefix="al_serialize_", dir=tmpdir)
            # write data into tmpfile
            try:
                with open(tmpfile, "wb") as f:
                    f.write(data[1:])
                # Temporarily open an ASCII backend for deserialization from tmpfile
                dbentry = DBEntry(ASCII_BACKEND, "serialize", 1, 1, "serialize")
                dbentry.open(options=f"-fullpath {tmpfile}")
                dbentry.get(self.metadata.name, destination=self)
            finally:
                # tmpfile may not exist depending if an error occurs in above code
                if os.path.exists(tmpfile):
                    os.unlink(tmpfile)
        else:
            raise ValueError(f"Unrecognized serialization protocol: {protocol}")

    def validate(self):
        """Validate the contents of this IDS.

        The following sanity checks are executed on this IDS:

        - The IDS must have a valid time mode (``ids_properties.homogeneous_time``)
        - For all non-empty quantities with coordinates:

            - If coordinates have an exact size (e.g. coordinate1 = 1...3), the size in
              that dimension must match this.
            - If coordinates refer to other elements (e.g. coordinate1 = time), the size
              in that dimension must be the same as the size of the referred quantity.

              Note that time is a special coordinate:

              - When using homogeneous time, the time coordinate is the /time node.
              - When using heterogeneous time, the time coordinate is the one specified
                by the coordinate. For dynamic Array of Structures, the time element is
                a FLT_0D inside the AoS (see ``profiles_1d`` in the core_profiles IDS).
                In such cases the time element must be set.
              - When using independent time mode, no time-dependent quantities may be
                set.

            - If a "same_as" coordinate is specified (e.g. coordinate2_same_as = r), the
              size in that dimension must be the same as the size in that dimension of
              the referred quantity.

        If any check fails, a ValidationError is raised that describes the problem.

        Example:

            >>> core_profiles = imaspy.IDSFactory().core_profiles()
            >>> core_profiles.validate()  # Did not set homogeneous_time
            [...]
            imaspy.exception.ValidationError: Invalid value for ids_properties/homogeneous_time: IDSPrimitive("/core_profiles/ids_properties/homogeneous_time", -999999999)
            >>> core_profiles.ids_properties.homogeneous_time = imaspy.ids_defs.IDS_TIME_MODE_HOMOGENEOUS
            >>> core_profiles.validate()  # No error: IDS is valid
            >>> core_profiles.profiles_1d.resize(1)
            >>> core_profiles.validate()
            [...]
            imaspy.exception.CoordinateError: Dimension 0 of element profiles_1d has incorrect size 1. Expected size is 0 (size of coordinate time).
            >>> core_profiles.time = [1]
            >>> core_profiles.validate()  # No error: IDS is valid

        """  # noqa: E501 (line too long)
        time_mode = self._time_mode
        if time_mode not in IDS_TIME_MODES:
            raise ValidationError(
                f"Invalid value for ids_properties/homogeneous_time: {time_mode.value}",
                {},
            )
        try:
            self._validate({})
        except ValidationError as exc:
            # hide recursive stack trace from user
            logger.debug("Original stack-trace of ValidationError: ", exc_info=1)
            raise exc.with_traceback(None) from None

    @needs_imas
    def get(self, occurrence: int = 0, db_entry: Optional["DBEntry"] = None) -> None:
        """Get data from UAL backend storage format and overwrite data in node

        Tries to dynamically build all needed information for the UAL. As this
        is the root node, it is simple to construct UAL paths and contexts at
        this level. Should have an open database.
        """
        if db_entry is None:
            raise NotImplementedError()
        db_entry.get(self.metadata.name, occurrence, destination=self)

    @needs_imas
    def getSlice(
        self,
        time_requested: float,
        interpolation_method: int,
        occurrence: int = 0,
        db_entry: Optional["DBEntry"] = None,
    ) -> None:
        """Get a slice from the backend.

        @param[in] time_requested time of the slice
        - UNDEFINED_TIME if not relevant (e.g to append a slice or replace the last slice)
        @param[in] interpolation_method mode for interpolation:
        - CLOSEST_INTERP take the slice at the closest time
        - PREVIOUS_INTERP take the slice at the previous time
        - LINEAR_INTERP interpolate the slice between the values of the previous and next slice
        - UNDEFINED_INTERP if not relevant (for write operations)
        """
        if db_entry is None:
            raise NotImplementedError()
        db_entry.get_slice(
            self.metadata.name,
            time_requested,
            interpolation_method,
            occurrence,
            destination=self,
        )

    @needs_imas
    def putSlice(
        self, occurrence: int = 0, db_entry: Optional["DBEntry"] = None
    ) -> None:
        """Put a single slice into the backend. only append is supported"""
        if db_entry is None:
            raise NotImplementedError()
        db_entry.put_slice(self, occurrence)

    @needs_imas
    def deleteData(
        self, occurrence: int = 0, db_entry: Optional["DBEntry"] = None
    ) -> None:
        """Delete UAL backend storage data

        Tries to dynamically build all needed information for the UAL. As this
        is the root node, it is simple to construct UAL paths and contexts at
        this level. Should have an open database.
        """
        if db_entry is None:
            raise NotImplementedError()
        db_entry.delete_data(self, occurrence)

    @needs_imas
    def put(self, occurrence: int = 0, db_entry: Optional["DBEntry"] = None) -> None:
        if db_entry is None:
            raise NotImplementedError()
        db_entry.put(self, occurrence)

    @needs_imas
    def partialGet(self, dataPath, occurrence=0):
        raise NotImplementedError(
            "{!s}.partialGet(dataPath, occurrence=0)".format(self)
        )

    def __repr__(self):
        abs_path = self._path  # Split this off here so that we can always decide
        # to get the abs_path from somewhere else
        assert abs_path.startswith("/"), (
            "Absolute path does not begin with" " a '/'. Is this a valid IDS?"
        )

        split_on_slash = self._path.split("/")
        ids_root = split_on_slash[1]

        my_repr = f"<{type(self).__name__}"
        my_repr += f" (IDS:{ids_root})>"

        return my_repr

    @cached_property
    def _toplevel(self) -> str:
        """Return the name of the toplevel"""
        return self.metadata.name
