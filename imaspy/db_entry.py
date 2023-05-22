# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.

import importlib
import logging
import os
from typing import Any, Optional

from imaspy.ids_data_type import IDSDataType
from imaspy.ids_defs import (
    CHAR_DATA,
    INTEGER_DATA,
    FORCE_CREATE_PULSE,
    CREATE_PULSE,
    FORCE_OPEN_PULSE,
    OPEN_PULSE,
    CLOSE_PULSE,
    ERASE_PULSE,
    READ_OP,
    WRITE_OP,
    IDS_TIME_MODE_HOMOGENEOUS,
    IDS_TIME_MODE_INDEPENDENT,
    IDS_TIME_MODE_UNKNOWN,
    IDS_TIME_MODES,
    MDSPLUS_BACKEND,
    UNDEFINED_INTERP,
    UNDEFINED_TIME,
    needs_imas,
)
from imaspy.ids_factory import IDSFactory
from imaspy.ids_mixin import IDSMixin
from imaspy.ids_metadata import IDSType
from imaspy.ids_structure import IDSStructure
from imaspy.ids_struct_array import IDSStructArray
from imaspy.ids_toplevel import IDSToplevel
from imaspy.mdsplus_model import ensure_data_dir, mdsplus_model_dir
from imaspy.ual_context import UalContext

logger = logging.getLogger(__name__)


class DBEntry:
    """Represents an IMAS database entry, which is a collection of stored IDSs."""

    @needs_imas
    def __init__(
        self,
        backend_id: int,
        db_name: str,
        shot: int,
        run: int,
        user_name: Optional[str] = None,
        data_version: Optional[str] = None,
        *,
        version: Optional[str] = None,
        xml_path: Optional[str] = None,
    ) -> None:
        """Create a new IMAS database entry object.

        You may use the optional arguments ``dd_version`` or ``xml_path`` to indicate
        the Data Dictionary version for usage with this Database Entry. If neither are
        supplied, the version is obtained from the IMAS_VERSION environment variable. If
        that also is not available, the latest available DD version is used.

        When using this DBEntry for reading data (:meth:`get` or :meth:`get_slice`), the
        returned IDSToplevel will be in the DD version specified. If the on-disk format
        is for a different DD version, the data is converted automatically.

        When using this DBEntry for writing data (:met:`put` or :meth:`put_slice`), the
        specified DD version is used for writing to the backend. If the provided
        IDSToplevel is for a different DD version, the data is converted automatically.

        Args:
            backend_id: ID of the backend to use, e.g. HDF5_BACKEND.
            db_name: Database name, e.g. "ITER".
            shot: Shot number of the database entry
            run: Run number of the database entry
            user_name: User name of the database, retrieved from environment when not
                supplied.
            data_version: Major version of the access layer, retrieved from environment
                when not supplied.
            dd_version: Data dictionary version to use.
            xml_path: Data dictionary definition XML file to use.
        """
        self.backend_id = backend_id
        self.db_name = db_name
        self.shot = shot
        self.run = run
        self.user_name = user_name or os.environ["USER"]
        self.data_version = data_version or os.environ["IMAS_VERSION"]
        self._db_ctx: Optional[UalContext] = None
        # TODO: don't import all of IMAS, only load _ual_lowlevel, see
        # https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
        self._ull = importlib.import_module("imas._ual_lowlevel")
        self._version = version
        self._xml_path = xml_path
        self._ids_factory = IDSFactory(version, xml_path)

    @property
    def factory(self):
        """Get the IDS factory used by this DB entry."""
        return self._ids_factory

    def _ual_open_pulse(self, mode: int, options: Any) -> None:
        """Internal method implementing open()/create()."""
        if self._db_ctx is not None:
            self.close()
        if self.backend_id == MDSPLUS_BACKEND:
            self._setup_mdsplus()
        status, idx = self._ull.ual_begin_pulse_action(
            self.backend_id,
            self.shot,
            self.run,
            self.user_name,
            self.db_name,
            self.data_version,
        )
        if status != 0:
            raise RuntimeError(f"Error calling ual_begin_pulse_action(), {status=}")
        self._db_ctx = UalContext(idx, self._ull)
        status = self._ull.ual_open_pulse(self._db_ctx.ctx, mode, options)
        if status != 0:
            raise RuntimeError(f"Error opening/creating database entry: {status=}")

    def _setup_mdsplus(self):
        """Additional setup required for MDSPLUS backend"""
        # Load the model directory of the IMAS version that we got instantiated with.
        # This does not cover the case of reading an idstoplevel and only then finding
        # out which version it is. But, I think that the model dir is not required if
        # there is an existing file.
        if self._version or self._xml_path:
            os.environ["ids_path"] = mdsplus_model_dir(self._version, self._xml_path)
        elif self._ids_factory._version:
            os.environ["ids_path"] = mdsplus_model_dir(self._ids_factory._version)
        else:
            # This doesn't actually matter much, since if we are auto-loading
            # the backend version it is an existing file and we don't need
            # the model (I think). If we are not auto-loading then one of
            # the above two conditions should be true.
            logger.warning(
                "No backend version information available, not building MDSPlus model."
            )

        # Note: MDSPLUS model directory only uses the major version component of
        # IMAS_VERSION, so we'll take the first character of IMAS_VERSION, or fallback
        # to "3" (older we don't support, newer is not available and probably never will
        # with Access Layer 4.x). This needs to be revised for AL5 either way, since the
        # directory structures are changing.
        version = self._version[0] if self._version else "3"
        ensure_data_dir(str(self.user_name), self.db_name, version, self.run)

    def close(self, *, options=None, erase=False):
        """Close this Database Entry.

        Args:
            options: Backend specific options. Defaults to None.
            erase: Remove the pulse file from the database. Defaults to False.
        """
        if self._db_ctx is None:
            return

        mode = ERASE_PULSE if erase else CLOSE_PULSE
        status = self._ull.ual_close_pulse(self._db_ctx.ctx, mode, options)
        if status != 0:
            raise RuntimeError(f"Error closing database entry: {status=}")

        self._ull.ual_end_action(self._db_ctx.ctx)
        self._db_ctx = None

    def create(self, *, options=None, force=True) -> None:
        """Create a new database entry.

        Caution:
            This method erases the previous entry if it existed!

        Args:
            options: Deprecated, available for backwards compatibility.
            force: Deprecated, available for backwards compatibility.

        Example:
            .. code-block:: python

                import imas
                from imas import imasdef

                imas_entry = imas.DBEntry("imas:hdf5?path=/home/ITER/username/public/imasdb/test/3/1/1234/")
                imas_entry.create()
        """  # noqa
        self._ual_open_pulse(FORCE_CREATE_PULSE if force else CREATE_PULSE, options)

    def open(self, *, options=None, force=False) -> None:
        """Open an existing database entry.

        Args:
            options: Deprecated, available for backwards compatibility.
            force: Deprecated, available for backwards compatibility.

        Example:
            .. code-block:: python

                import imas
                from imas import imasdef

                imas_entry = imas.DBEntry("imas:hdf5?path=/home/ITER/username/public/imasdb/test/3/1/1234/")
                imas_entry.open()
        """  # noqa
        self._ual_open_pulse(FORCE_OPEN_PULSE if force else OPEN_PULSE, options)

    def get(self, ids_name: str, occurrence: int = 0) -> IDSToplevel:
        """Read the contents of the an IDS into memory.

        This method fetches an IDS in its entirety, with all time slices it may contain.
        See :meth:`get_slice` for reading a specific time slice.

        Empty fields within the IDS in the Data Entry are returned with the default
        values indicated in :ref:`Empty fields`.

        Args:
            ids_name: Name of the IDS to read from the backend.
            occurrence: Which occurrence of the IDS to read. Defaults to 0.

        Returns:
            The loaded IDS.

        Example:
            .. code-block:: python

                import imas
                from imas import imasdef

                imas_entry = imas.DBEntry("imas:mdsplus?user=public;shot=131024;run=41;database=ITER")
                imas_entry.open()
                core_profiles = imas_entry.get("core_profiles")
        """  # noqa
        return self._get(ids_name, occurrence, None, 0)

    def get_slice(
        self,
        ids_name: str,
        time_requested: float,
        interpolation_method: int,
        occurrence: int = 0,
    ) -> IDSToplevel:
        """Read a single time slice from an IDS in this Database Entry.

        This method returns an IDS object with all constant/static data filled. The
        dynamic data is interpolated on the requested time slice. This means that the
        size of the time dimension in the returned data is 1.

        Args:
            ids_name: Name of the IDS to read from the backend.
            time_requested: Requested time slice
            interpolation_method: Interpolation method to use. Available options:

                - :const:`~imas.imasdef.CLOSEST_INTERP`
                - :const:`~imas.imasdef.PREVIOUS_INTERP`
                - :const:`~imas.imasdef.LINEAR_INTERP`

            occurrence: Which occurrence of the IDS to read. Defaults to 0.

        Returns:
            The loaded IDS.

        Example:
            .. code-block:: python

                import imas
                from imas import imasdef

                imas_entry = imas.DBEntry("imas:mdsplus?user=public;shot=131024;run=41;database=ITER")
                imas_entry.open()
                core_profiles = imas_entry.get_slice("core_profiles", 370, imasdef.PREVIOUS_INTERP)
        """  # noqa
        return self._get(ids_name, occurrence, time_requested, interpolation_method)

    def _get(
        self,
        ids_name: str,
        occurrence: int,
        time_requested: Optional[float],
        interpolation_method: int,
    ) -> IDSToplevel:
        """Actual implementation of get() and get_slice()"""
        if self._db_ctx is None:
            raise RuntimeError("Database entry is not opened, use open() first.")
        ll_path = ids_name
        if occurrence != 0:
            ll_path += f"/{occurrence}"

        with self._db_ctx.global_action(ll_path, READ_OP) as read_ctx:
            dd_version = read_ctx.read_data(
                "ids_properties/version_put/data_dictionary", "", CHAR_DATA, 1
            )
            time_mode = read_ctx.read_data(
                "ids_properties/homogeneous_time", "", INTEGER_DATA, 0
            )
        if time_mode not in IDS_TIME_MODES:
            raise RuntimeError()  # FIXME!

        if not dd_version:
            logger.warning(
                "Loaded IDS (%s, occurrence %s) does not specify a data dictionary "
                "version. Some data may not be loaded.",
                ids_name,
                occurrence,
            )
        elif dd_version != self._ids_factory._version:
            raise NotImplementedError("DD version conversion is not yet implemented.")
        # Create a new IDSToplevel with the same version as stored in the backend
        toplevel = self._ids_factory.new(ids_name)
        # Now fill the IDSToplevel
        if time_requested is None:  # get
            manager = self._db_ctx.global_action(ll_path, READ_OP)
        else:  # get_slice
            manager = self._db_ctx.slice_action(
                ll_path, READ_OP, time_requested, interpolation_method
            )
        with manager as read_ctx:
            _get_children(toplevel, read_ctx, time_mode, "")
        return toplevel

    def put(self, ids: IDSToplevel, occurrence: int = 0) -> None:
        """Write the contents of an IDS into this Database Entry.

        The IDS is written entirely, with all time slices it may contain.

        The IDS object can have none or many empty fields, empty fields are ignored and
        remain empty in the data entry. Some fields are required to be filled before
        calling this method, see :ref:`Empty fields`.

        Caution:
            The put method deletes any previously existing data within the target IDS
            occurrence in the Database Entry.

        Args:
            ids: IDS object to put.
            occurrence: Which occurrence of the IDS to write to. Defaults to 0.

        Example:
            .. code-block:: python

                ids = imas.pf_active()
                ...  # fill the pf_active IDS here
                imas_entry.put(ids)
        """
        self._put(ids, occurrence, False)

    def put_slice(self, ids: IDSToplevel, occurrence: int = 0) -> None:
        """Append a time slice of the provided IDS to the Database Entry.

        A frequent use case is the simulation of time evolution, in which one has to put
        the constant and static values only once and then progressively append the
        subsequent dynamic values calculated at each loop step. In such use case it is
        expected that the IDS variable contains one or more time slices to be appended
        to the already stored part of the IDS, in any non-empty dynamic node. It's thus
        possible to append several time slices to a node of the IDS in one PUT_SLICE
        call, however the user must ensure that the size of the time dimension of the
        node remains consistent with the size of its timebase. An initial call to the
        PUT function at the first iteration of the loop will first delete any previously
        existing data within the target IDS occurrence in the Data Entry and then put
        simultaneously the constant/static and the dynamic data of the IDS variable.
        Then the PUT_SLICE function should be called for every subsequent iteration of
        the loop, which will append the content of the non-empty dynamic nodes of the
        IDS variable to the time dimension of the nodes in the stored IDS.

        PUT_SLICE does not require anymore the IDS to be in homogeneous mode (previous
        limitation of Access Layer 3.x versions). Timebases with different values and
        sizes can be appended. By not allocating some dynamic nodes in the IDS variable
        for some iterations of the time loop (e.g. slowly-varying quantities), it is
        possible to skip appending to them a value, thus enabling to construct an IDS
        containing time bases with different sizes with a series of PUT_SLICE calls.

        Time slices must be appended in strictly increasing time order, since the Access
        Layer is not reordering time arrays. Doing otherwise will result in
        non-monotonic time arrays, which will create confusion and make subsequent
        GET_SLICE commands to fail.

        Although being put progressively time slice by time slice, the final IDS must be
        compliant with the data dictionary. A typical error when constructing IDS
        variables time slice by time slice is to change the size of the IDS fields
        during the time loop, which is not allowed but for the children of an array of
        structure which has time as its coordinate.

        The PUT_SLICE command is appending data, so does not modify previously existing
        data within the target IDS occurrence in the Data Entry

        Args:
            ids: IDS object to put.
            occurrence: Which occurrence of the IDS to write to. Defaults to 0.

        Example:
            .. code-block:: python

                ids = imas.pf_active()
                ...  # fill the static data of the pf_active IDS here
                for i in range(N):
                    ... # fill time slice of the pf_active IDS
                    imas_entry.put_slice(ids)
        """
        self._put(ids, occurrence, True)

    def _put(self, ids: IDSToplevel, occurrence: int, is_slice: bool):
        """Actual implementation of put() and put_slice()"""
        if self._db_ctx is None:
            raise RuntimeError("Database entry is not opened, use open() first.")

        if not ids._parent or ids._parent._version != self._ids_factory._version:
            raise NotImplementedError("DD version conversion is not yet implemented.")

        # Verify homogeneous_time is set
        time_mode = ids.ids_properties.homogeneous_time
        # TODO: allow unset homogeneous_time and quit with no action?
        if time_mode not in IDS_TIME_MODES:
            raise ValueError("'ids_properties.homogeneous_time' is not set or invalid.")
        if is_slice and time_mode == IDS_TIME_MODE_INDEPENDENT:
            raise RuntimeError("Cannot use put_slice with IDS_TIME_MODE_INDEPENDENT.")

        ll_path = ids.metadata.name
        if occurrence != 0:
            ll_path += f"/{occurrence}"

        if hasattr(ids.ids_properties, "version_put"):  # Only available in DD 3.22+
            version_put = ids.ids_properties.version_put
            version_put.data_dictionary = ids._version
            # TODO! AL version
            version_put.access_layer_language

        if is_slice:
            with self._db_ctx.global_action(ll_path, READ_OP) as read_ctx:
                db_time_mode = read_ctx.read_data(
                    "ids_properties/homogeneous_time", "", INTEGER_DATA, 0
                )
            if db_time_mode == IDS_TIME_MODE_UNKNOWN:
                # No data yet on disk, so just put everything
                is_slice = False
            elif db_time_mode != time_mode:
                raise RuntimeError(
                    f"Cannot change homogeneous_time from {db_time_mode} to {time_mode}"
                )

        if not is_slice:
            # put() must first delete any existing data
            with self._db_ctx.global_action(ll_path, WRITE_OP) as write_ctx:
                _delete_children(ids, write_ctx, "")
        if is_slice:
            manager = self._db_ctx.slice_action(
                ll_path, WRITE_OP, UNDEFINED_TIME, UNDEFINED_INTERP
            )
        else:
            manager = self._db_ctx.global_action(ll_path, WRITE_OP)
        with manager as write_ctx:
            _put_children(ids, write_ctx, time_mode, "", is_slice)


def _get_children(
    structure: IDSStructure, ctx: UalContext, time_mode: int, ctx_path: str
) -> None:
    """Recursively get all children of an IDSStructure"""
    for element in structure:
        if (
            time_mode == IDS_TIME_MODE_INDEPENDENT
            and element.metadata.type is IDSType.DYNAMIC
        ):
            # skip dynamic (time-dependent) nodes
            continue

        name = element.metadata.name
        new_path = f"{ctx_path}/{name}" if ctx_path else name

        if isinstance(element, IDSStructArray):
            timebase = _get_timebasepath(element, time_mode, new_path)
            with ctx.arraystruct_action(new_path, timebase, 0) as (new_ctx, size):
                if size > 0:  # FIXME: resizing an empty aos to 0 raises an error
                    element.resize(size)
                for item in element:
                    _get_children(item, new_ctx, time_mode, "")
                    new_ctx.iterate_over_arraystruct(1)

        elif isinstance(element, IDSStructure):
            _get_children(element, ctx, time_mode, new_path)

        else:  # Data elements
            data_type = element.metadata.data_type
            ndim = element.metadata.ndim
            if data_type is IDSDataType.STR:
                ndim += 1  # STR_0D is a 1D CHARACTER type...
            timebase = _get_timebasepath(element, time_mode, new_path)
            data = ctx.read_data(new_path, timebase, data_type.ual_type, ndim)
            if data is not None:
                element.value = data


def _delete_children(structure: IDSStructure, ctx: UalContext, ctx_path: str) -> None:
    """Recursively delete all children of an IDSStructure"""
    for element in structure:
        name = element.metadata.name
        new_path = f"{ctx_path}/{name}" if ctx_path else name
        # FIXME: `and not` clause can be removed when IDSStructArray no longer inherits
        # from IDSStructure.
        if isinstance(element, IDSStructure) and not isinstance(IDSStructArray):
            _delete_children(element, ctx, new_path)
        else:  # Data elements and IDSStructArray
            ctx.delete_data(new_path)


def _put_children(
    structure: IDSStructure,
    ctx: UalContext,
    time_mode: int,
    ctx_path: str,
    is_slice: bool,
) -> None:
    """Recursively put all children of an IDSStructure"""
    # Note: when putting a slice, we do not need to descend into IDSStructure and
    # IDSStructArray elements if they don't contain dynamic data nodes. That is hard to
    # detect now, so we just recurse and check the data elements
    for element in structure:
        if (
            element.metadata.type is IDSType.DYNAMIC
            and time_mode == IDS_TIME_MODE_INDEPENDENT
        ):
            continue  # skip dynamic data when in time independent mode
        name = element.metadata.name
        new_path = f"{ctx_path}/{name}" if ctx_path else name

        if isinstance(element, IDSStructArray):
            timebase = _get_timebasepath(element, time_mode, new_path)
            size = len(element.value)
            with ctx.arraystruct_action(new_path, timebase, size) as (new_ctx, _):
                for item in element:
                    _put_children(item, new_ctx, time_mode, "", is_slice)
                    new_ctx.iterate_over_arraystruct(1)

        elif isinstance(element, IDSStructure):
            _put_children(element, ctx, time_mode, new_path, is_slice)

        else:  # Data elements
            if is_slice and element.metadata.type is not IDSType.DYNAMIC:
                continue  # put_slice only stores dynamic data
            timebase = _get_timebasepath(element, time_mode, new_path)
            if element.has_value:  # TODO: this should return False when set to default?
                ctx.write_data(new_path, timebase, element.value)


def _get_timebasepath(ele: IDSMixin, time_mode: int, ctx_path: str) -> str:
    """Calculate the timebasepath to use for the lowlevel."""
    if isinstance(ele, IDSStructArray):
        # https://git.iter.org/projects/IMAS/repos/access-layer/browse/pythoninterface/py_ids.xsl?at=refs%2Ftags%2F4.11.4#367-384
        if ele.metadata.type is not IDSType.DYNAMIC:
            return ""
        timebasepath = ctx_path + "/time"
    else:  # IDSPrimitive
        # https://git.iter.org/projects/IMAS/repos/access-layer/browse/pythoninterface/py_ids.xsl?at=refs%2Ftags%2F4.11.4#1524-1566
        if ele.metadata.type is not IDSType.DYNAMIC or ele._parent._is_dynamic:
            return ""
        timebasepath = ele.metadata.timebasepath
    if time_mode == IDS_TIME_MODE_HOMOGENEOUS:
        return "/time"
    # IDS_TIME_MODE_HETEROGENEOUS
    return timebasepath
