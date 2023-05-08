# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Represents a Top-level IDS (like NBI etc)
* :py:class:`IDSToplevel`
"""

# Set up logging immediately

from packaging.version import Version as V
import contextlib
import tempfile
import os

import numpy as np

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from imaspy.setup_logging import root_logger as logger
from imaspy.al_exception import ALException
from imaspy.context_store import context_store
from imaspy.dd_zip import dd_etree
from imaspy.ids_structure import IDSStructure

from imaspy.ids_defs import (
    ASCII_BACKEND,
    ASCII_SERIALIZER_PROTOCOL,
    CHAR_DATA,
    CLOSEST_INTERP,
    DEFAULT_SERIALIZER_PROTOCOL,
    EMPTY_INT,
    IDS_TIME_MODE_HETEROGENEOUS,
    IDS_TIME_MODE_HOMOGENEOUS,
    IDS_TIME_MODE_INDEPENDENT,
    IDS_TIME_MODE_UNKNOWN,
    IDS_TIME_MODES,
    INTEGER_DATA,
    LINEAR_INTERP,
    PREVIOUS_INTERP,
    READ_OP,
    UNDEFINED_INTERP,
    UNDEFINED_TIME,
    WRITE_OP,
    needs_imas,
)


class IDSToplevel(IDSStructure):
    """This is any IDS Structure which has ids_properties as child node

    At minimum, one should fill ids_properties/homogeneous_time
    IF a quantity is filled, the coordinates of that quantity must be filled as well
    """

    def __init__(
        self, parent, structure_xml, backend_version=None, backend_xml_path=None
    ):
        """Save backend_version and backend_xml and build translation layer.

        Args:
            parent: Parent of ``self``. Usually an instance of :py:class:`IDSRoot`.
            name: Name of this structure. Usually from the ``name`` attribute of
                the IDS toplevel definition.
            structure_xml: XML structure that defines this IDS toplevel.
            backend_version: Version of the Data Dictionary used in the
                backend to read/write. See :py:class:`IDSRoot`.
            backend_xml_path: Explicit path the the DD of the backend
                ``IDSRoot.xml``. Overwrites ``version`` similar to ``xml_path``.
                See :py:class:`IDSRoot`.
        """
        super().__init__(parent, structure_xml)

        # Set an explicit backend_version or xml path
        # these will be used when put() or get() is called.
        self._backend_version = backend_version
        self._backend_xml_path = backend_xml_path

        if backend_xml_path or backend_version:
            self._read_backend_xml(backend_version, backend_xml_path)

    def _read_backend_xml(self, version=None, xml_path=None):
        """Find a DD xml from version or path, select the child corresponding to the
        current name and set the backend properties.

        This is defined on the Toplevel and not on the Root because that allows
        IDSes to be read from different versions. Still use the ElementTree memoization
        so performance will not suffer too much from this.
        """
        if xml_path is not None:
            self._backend_xml_path = xml_path
            logger.info(
                "Generating backend %s from file %s", self.metadata.name, xml_path
            )
        elif version is not None:
            self._backend_version = version
            logger.info(
                "Generating backend %s for version %s", self.metadata.name, version
            )
        else:
            return
        tree = dd_etree(version=version, xml_path=xml_path)

        # Parse given xml_path and build imaspy IDS structures for this toplevel only
        root = tree.getroot()
        ver = root.find("version")
        if ver is not None:
            if ver.text != version:
                if version is None:
                    self._backend_version = ver.text
                    logger.info("Found backend version %s", self._backend_version)
                else:
                    logger.warning(
                        "Backend version %s does not match file %s, proceeding anyway.",
                        version,
                        ver.text,
                    )
        else:
            # The version number in DD xml files was introduced in 3.30.0
            if version is not None and V(version) >= V("3.30.0"):
                logger.warning("No version number found in file %s", xml_path)

        self.set_backend_properties(
            root.find("./*[@name='{name}']".format(name=self.metadata.name))
        )

    @property
    def _time_mode(self) -> int:
        """Retrieve the time mode from `/ids_properties/homogeneous_time`"""
        return self.ids_properties.homogeneous_time

    def set_backend_properties(self, structure_xml):
        """Set backend properties for this IDSToplevel and provide some logging"""
        # TODO: better naming (structure_xml -> backend etc)
        # TODO: warn if backend xmls are not found in memory, so that you know
        # what you are missing?

        # change_nbc_version was introduced in version 3.28.0 (with changes
        # going back to 3.26.0). For versions older than that there is no
        # rename information available!
        if (
            self._version
            and self._backend_version
            and max(V(self._version), V(self._backend_version)) < V("3.28.0")
        ):
            logger.warning(
                "Rename information was added in 3.28.0. It is highly "
                "recommended to at least use this version."
            )

        super().set_backend_properties(structure_xml)

    @staticmethod
    def default_serializer_protocol():
        """Return the default serializer protocol."""
        return DEFAULT_SERIALIZER_PROTOCOL

    @contextlib.contextmanager
    def _serialize_open_temporary_backend(self, *args, **kwargs):
        """Helper context manager to open a temporary backend.

        All arguments are forwarded to :meth:`IDSRoot.create_env_backend`.
        """
        # these state variables are overwritten in create_env_backend
        current_backend_state = (
            self._parent.connected,
            self._parent.expIdx,
            getattr(self._parent, "_data_store", None),  # _data_store may not exist
        )
        self._parent.create_env_backend(*args, **kwargs)
        try:
            yield
        finally:
            # close the temporary backend
            self._parent._data_store.close()
            # restore state
            (
                self._parent.connected,
                self._parent.expIdx,
                self._parent._data_store,
            ) = current_backend_state

    @needs_imas
    def serialize(self, protocol=None):
        """Serialize this IDS to a data buffer.

        The data buffer can be deserialized from any Access Layer High-Level Interface
        that supports this. Currently known to be: IMASPy, Python, C++ and Fortran.

        Example:

        .. code-block: python

            data_entry = imaspy.ids_root.IDSRoot(1, 0)
            core_profiles = data_entry.core_profiles
            # fill core_profiles with data
            ...

            data = core_profiles.serialize()

            # For example, send `data` to another program with libmuscle.
            # Then deserialize on the receiving side:

            data_entry = imaspy.ids_root.IDSRoot(1, 0)
            core_profiles = data_entry.core_profiles
            core_profiles.deserialize(data)
            # Use core_profiles:
            ...

        Args:
            protocol: Which serialization protocol to use. Currently only
                ASCII_SERIALIZER_PROTOCOL is supported.
                Defaults to DEFAULT_SERIALIZER_PROTOCOL.

        Returns:
            Data buffer that can be deserialized using :meth:`deserialize`.
        """
        if protocol is None:
            protocol = self.default_serializer_protocol()
        if self.ids_properties.homogeneous_time == IDS_TIME_MODE_UNKNOWN:
            raise ALException("IDS is found to be EMPTY (homogeneous_time undefined)")
        if protocol == ASCII_SERIALIZER_PROTOCOL:
            tmpdir = "/dev/shm" if os.path.exists("/dev/shm") else "."
            tmpfile = tempfile.mktemp(prefix="al_serialize_", dir=tmpdir)
            # Temporarily open an ASCII backend for serialization to tmpfile
            with self._serialize_open_temporary_backend(
                "serialize",
                "serialize",
                "3",
                ASCII_BACKEND,
                options=f"-fullpath {tmpfile}",
            ):
                self.put()
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
            tmpdir = "/dev/shm" if os.path.exists("/dev/shm") else "."
            tmpfile = tempfile.mktemp(prefix="al_serialize_", dir=tmpdir)
            # write data into tmpfile
            try:
                with open(tmpfile, "wb") as f:
                    f.write(data[1:])
                # Temporarily open an ASCII backend for deserialization from tmpfile
                with self._serialize_open_temporary_backend(
                    "serialize",
                    "serialize",
                    "3",
                    ASCII_BACKEND,
                    options=f"-fullpath {tmpfile}",
                ):
                    self.get()
            finally:
                # tmpfile may not exist depending if an error occurs in above code
                if os.path.exists(tmpfile):
                    os.unlink(tmpfile)
        else:
            raise ValueError(f"Unrecognized serialization protocol: {protocol}")

    def readHomogeneous(self, occurrence, always_read=False):
        """Read the value of homogeneousTime

        Returns:
            0: IDS_TIME_MODE_HETEROGENEOUS; Dynamic nodes may be asynchronous,
               their timebase is located as indicated in the "Coordinates"
               column of the documentation
            1: IDS_TIME_MODE_HOMOGENEOUS; All dynamic nodes are synchronous,
               their common timebase is the "time" node that is the child of
               the nearest parent IDS
            2: IDS_TIME_MODE_INDEPENDENT; No dynamic node is filled in the IDS
               (dynamic nodes _will_ be skipped by the Access Layer)
        """
        homogeneousTime = IDS_TIME_MODE_UNKNOWN
        if occurrence == 0:
            path = self.metadata.name
        else:
            path = self.metadata.name + "/" + str(occurrence)

        # only read from the backend if it is not defined locally.
        homogeneousTime = self.ids_properties.homogeneous_time.value

        if homogeneousTime in [EMPTY_INT, IDS_TIME_MODE_UNKNOWN] or always_read:
            status, ctx = self._ull.ual_begin_global_action(self._idx, path, READ_OP)
            context_store[ctx] = context_store[self._idx] + "/" + path
            if status != 0:
                raise ALException(
                    "Error calling ual_begin_global_action() in readHomogeneous()"
                    "operation",
                    status,
                )

            status, homogeneousTime = self._ull.ual_read_data(
                ctx, "ids_properties/homogeneous_time", "", INTEGER_DATA, 0
            )

            if status != 0:
                raise ALException("ERROR: homogeneous_time cannot be read.", status)

            status = self._ull.ual_end_action(ctx)
            context_store.pop(ctx)

            if status != 0:
                raise ALException(
                    "Error calling ual_end_action() in readHomogeneous() operation",
                    status,
                )
        return homogeneousTime

    @needs_imas
    def read_data_dictionary_version(self, occurrence):
        data_dictionary_version = ""
        path = self.metadata.name
        if occurrence != 0:
            path += "/" + str(occurrence)

        status, ctx = self._ull.ual_begin_global_action(self._idx, path, READ_OP)
        context_store[ctx] = context_store[self._idx] + "/" + path
        if status != 0:
            raise ALException(
                "Error calling ual_begin_global_action() in read_data_dictionary_version() operation",
                status,
            )

        status, data_dictionary_version = self._ull.ual_read_data_string(
            ctx, "ids_properties/version_put/data_dictionary", "", CHAR_DATA, 1
        )
        if status != 0:
            raise ALException("ERROR: data_dictionary_version cannot be read.", status)
        status = self._ull.ual_end_action(ctx)
        context_store.pop(ctx)
        if status != 0:
            raise ALException(
                "Error calling ual_end_action() in read_data_dictionary_version() operation",
                status,
            )
        return data_dictionary_version

    @needs_imas
    def get(self, occurrence=0, ctx=None, **kwargs):
        """Get data from UAL backend storage format and overwrite data in node

        Tries to dynamically build all needed information for the UAL. As this
        is the root node, it is simple to construct UAL paths and contexts at
        this level. Should have an open database.
        """
        path = None
        if occurrence == 0:
            path = self.metadata.name
        else:
            path = self.metadata.name + "/" + str(occurrence)

        homogeneousTime = self.readHomogeneous(occurrence)
        if homogeneousTime not in IDS_TIME_MODES:
            logger.error(
                "Unknown time mode %s, stop getting of %s",
                homogeneousTime,
                self.metadata.name,
            )
            return

        backend_version = self.read_data_dictionary_version(occurrence)
        if self._backend_xml_path:
            # If we have specified a preference backend_version is completely ignored.
            logger.info("using backend_xml_path %s", self._backend_xml_path)
        elif self._backend_version:
            # If we have specified a preference:
            if backend_version != self._backend_version:
                logger.warning(
                    "Specified backend version '%s' does not "
                    "correspond to version_put '%s'",
                    self._backend_version,
                    backend_version,
                )
                backend_version = self._backend_version
            logger.info("using backend_version %s", self._backend_version)

        # building the backend_xml is only necessary in some cases
        if self._backend_xml_path or (
            backend_version and backend_version != self._parent._imas_version
        ):
            self._read_backend_xml(
                version=backend_version, xml_path=self._backend_xml_path
            )

        if ctx is None:
            status, ctx = self._ull.ual_begin_global_action(
                self._idx, path.lstrip("/"), READ_OP
            )
            if status != 0:
                raise ALException(
                    "Error calling ual_begin_global_action() for {!s}".format(
                        self.metadata.name
                    ),
                    status,
                )
            context_store[ctx] = context_store[self._idx] + path

        logger.debug("{:53.53s} get".format(self.metadata.name))
        super().get(ctx, homogeneousTime, **kwargs)

        status = self._ull.ual_end_action(ctx)
        context_store.pop(ctx)
        if status != 0:
            raise ALException(
                "Error calling ual_end_action() for {!s}".format(self.metadata.name),
                status,
            )

    @needs_imas
    def getSlice(
        self, time_requested, interpolation_method=CLOSEST_INTERP, occurrence=0
    ):
        """Get a slice from the backend.

        @param[in] time_requested time of the slice
        - UNDEFINED_TIME if not relevant (e.g to append a slice or replace the last slice)
        @param[in] interpolation_method mode for interpolation:
        - CLOSEST_INTERP take the slice at the closest time
        - PREVIOUS_INTERP take the slice at the previous time
        - LINEAR_INTERP interpolate the slice between the values of the previous and next slice
        - UNDEFINED_INTERP if not relevant (for write operations)
        """
        if occurrence == 0:
            path = self._path
        else:
            path = self._path + "/" + str(occurrence)

        if interpolation_method not in [
            CLOSEST_INTERP,
            LINEAR_INTERP,
            PREVIOUS_INTERP,
            UNDEFINED_INTERP,
        ]:
            logger.error(
                "getSlice called with unexpected interpolation method %s",
                interpolation_method,
            )

        self._is_slice = True
        status, ctx = self._ull.ual_begin_slice_action(
            self._idx, path.lstrip("/"), READ_OP, time_requested, interpolation_method
        )
        if status != 0:
            raise ALException(
                "Error calling ual_begin_slice_action() for {!s}".format(path),
                status,
            )
        context_store[ctx] = context_store[self._idx].rstrip("/") + path

        self.get(ctx=ctx)

    @needs_imas
    def putSlice(self, occurrence=0, ctx=None):
        """Put a single slice into the backend. only append is supported"""
        homogeneousTime = self.readHomogeneous(occurrence=occurrence)
        if homogeneousTime == IDS_TIME_MODE_UNKNOWN:
            logger.error("%s has unknown homogeneous_time, putSlice aborts", self._path)
            return
        if homogeneousTime not in IDS_TIME_MODES:
            raise ALException(
                "ERROR: ids_properties.homogeneous_time={!s} should be set to "
                "IDS_TIME_MODE_HETEROGENEOUS, IDS_TIME_MODE_HOMOGENEOUS or "
                "IDS_TIME_MODE_INDEPENDENT.".format(homogeneousTime)
            )
        if homogeneousTime == IDS_TIME_MODE_HOMOGENEOUS and len(self.time.value) == 0:
            raise ALException(
                "ERROR: the IDS%time vector of an homogeneous_time IDS must have a non-zero length."
            )
            return
        if homogeneousTime == IDS_TIME_MODE_INDEPENDENT:
            raise NotImplementedError(
                "homogeneous_time=independent not implemented for putSlice."
            )

        stored_time_mode = self.readHomogeneous(occurrence=occurrence, always_read=True)
        if stored_time_mode == IDS_TIME_MODE_UNKNOWN:
            logger.info(
                "Slice is added to an empty IDS %s, calling PUT instead",
                self.metadata.name,
            )

            # put only static and constant quantities, and use putSlice below
            # for the rest
            # self.put(occurrence=occurrence, types=["static", "constant"])

            # as a workaround, instead of the above, we do a 'full' put()
            # now, and do not write this slice completely.
            # there is an issue with the MDSPlus backend which forces us to do
            # that, since adding a slice to an empty list is not appreciated.
            self.put(occurrence=occurrence)
            # we then have to stop, before we write the slice twice
            return

        path = "/" + self.metadata.name

        self._is_slice = True

        status, ctx = self._ull.ual_begin_slice_action(
            self._idx, path.lstrip("/"), WRITE_OP, UNDEFINED_TIME, UNDEFINED_INTERP
        )
        if status != 0:
            raise ALException(
                "Error calling ual_begin_slice_action() for {!s}".format(path),
                status,
            )
        context_store[ctx] = context_store[self._idx].rstrip("/") + path

        # write only values where type == dynamic
        # time is dynamic, so that gets updated
        # nota bene that this does not call IDSToplevel's put, but IDSStructure's
        super().put(ctx, homogeneousTime, types=["dynamic"])

        status = self._ull.ual_end_action(ctx)
        if status != 0:
            raise ALException(
                "Error calling ual_end_action() for {!s}".format(path),
                status,
            )
        context_store.pop(ctx)

    @needs_imas
    def deleteData(self, occurrence=0):
        """Delete UAL backend storage data

        Tries to dynamically build all needed information for the UAL. As this
        is the root node, it is simple to construct UAL paths and contexts at
        this level. Should have an open database.
        """
        if not np.issubdtype(type(occurrence), np.integer):
            raise ValueError("Occurrence should be an integer")

        rel_path = self.getRelCTXPath(self._idx)
        if occurrence != 0:
            rel_path += "/" + str(occurrence)

        status, ctx = self._ull.ual_begin_global_action(self._idx, rel_path, WRITE_OP)
        context_store[ctx] = context_store[self._idx] + rel_path
        if status < 0:
            raise ALException(
                'ERROR: ual_begin_global_action failed for "{!s}"'.format(rel_path),
                status,
            )

        super().delete(ctx)

        status = self._ull.ual_end_action(ctx)
        context_store.pop(ctx)
        if status < 0:
            raise ALException(
                'ERROR: ual_end_action failed for "{!s}"'.format(rel_path), status
            )
        return 0

    @needs_imas
    def to_ualstore(self, ual_data_store, path=None, occurrence=0, **kwargs):
        """Put data into UAL backend storage format

        As all children _should_ support being put, just call `put` blindly.

        Tries to dynamically build all needed information for the UAL. As this
        is the root node, it is simple to construct UAL paths and contexts at
        this level. Should have an open database.
        """
        if path is not None:
            raise NotImplementedError("Explicit paths, implicitly handled by structure")
        path = "/" + self.metadata.name

        if occurrence != 0:
            path += "/" + str(occurrence)

        # Determine the time_mode.
        homogeneousTime = self.readHomogeneous(occurrence=occurrence)
        if (
            homogeneousTime == IDS_TIME_MODE_UNKNOWN
            or homogeneousTime == EMPTY_INT
            or homogeneousTime is None
        ):
            logger.error(
                "IDS {!s} is found to be empty (homogeneous_time undefined). "
                "PUT quits with no action.".format(self._path)
            )
            return
        if homogeneousTime not in IDS_TIME_MODES:
            raise ALException(
                "ERROR: ids_properties.homogeneous_time {!s} should be set to "
                "IDS_TIME_MODE_HETEROGENEOUS {!s}, IDS_TIME_MODE_HOMOGENEOUS {!s} "
                "or IDS_TIME_MODE_INDEPENDENT {!s}.".format(
                    homogeneousTime,
                    IDS_TIME_MODE_HETEROGENEOUS,
                    IDS_TIME_MODE_HOMOGENEOUS,
                    IDS_TIME_MODE_INDEPENDENT,
                )
            )

        # Delete the data in the store
        # TODO: handle mode correctly!
        self.deleteData(occurrence)

        # Begin a write action
        status, ctx = self._ull.ual_begin_global_action(
            self._idx, path.lstrip("/"), WRITE_OP
        )
        if status != 0:
            raise ALException(
                "Error {!s} calling ual_begin_global_action() for {!s}".format(
                    status,
                    self.metadata.name,
                )
            )
        context_store[ctx] = path

        super().put(ctx, homogeneousTime, **kwargs)

        context_store.pop(ctx)
        status = self._ull.ual_end_action(ctx)
        if status != 0:
            raise ALException(
                "Error calling ual_end_action() for {!s}".format(self.metadata.name),
                status,
            )

    def setExpIdx(self, idx):
        logger.warning(
            "setExpIdx is deprecated, call self.setPulseCtx instead", FutureWarning
        )
        self.setPulseCtx(idx)

    @needs_imas
    def put(self, occurrence=0, data_store=None, **kwargs):
        if data_store is None:
            data_store = self._data_store
        if hasattr(self.ids_properties, "version_put"):
            self.ids_properties.version_put.data_dictionary = (
                self._backend_version or self._version
            )
            # TODO: self.ids_properties.version_put.access_layer =  # get the access layer version number here
            self.ids_properties.version_put.access_layer_language = "Python"
        self.to_ualstore(data_store, path=None, occurrence=occurrence, **kwargs)

    @property
    def _data_store(self):
        return self._parent._data_store

    @property
    def _idx(self):
        return self._data_store._idx

    @cached_property
    def backend_version(self):
        return self.__getattribute__("_backend_version")

    @classmethod
    def getMaxOccurrences(self):
        raise NotImplementedError("{!s}.getMaxOccurrences()".format(self))
        return cls._MAX_OCCURRENCES

    def initIDS(self):
        raise NotImplementedError("{!s}.initIDS()".format(self))

    @needs_imas
    def partialGet(self, dataPath, occurrence=0):
        raise NotImplementedError(
            "{!s}.partialGet(dataPath, occurrence=0)".format(self)
        )

    def getField(self, dataPath, occurrence=0):
        raise NotImplementedError("{!s}.getField(dataPath, occurrence=0)".format(self))

    def _getFromPath(self, dataPath, occurrence, analyzeTime, data_store=None):
        # Retrieve partial IDS data without reading the full database content
        raise NotImplementedError(
            "{!s}.getField(dataPath, occurrence, analyzeTime, data_store=None)".format(
                self
            )
        )
