# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

import logging
import os
from typing import Any, List, Optional, Tuple, overload
from urllib.parse import urlparse

import imaspy
from imaspy.exception import ValidationError
from imaspy.ids_convert import dd_version_map_from_factories
from imaspy.ids_defs import (
    ASCII_BACKEND,
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
    IDS_TIME_MODE_INDEPENDENT,
    IDS_TIME_MODE_UNKNOWN,
    IDS_TIME_MODES,
    MDSPLUS_BACKEND,
    UNDEFINED_INTERP,
    UNDEFINED_TIME,
    needs_imas,
)
from imaspy.ids_factory import IDSFactory
from imaspy.ids_metadata import IDSType
from imaspy.ids_mixin import IDSMixin
from imaspy.ids_toplevel import IDSToplevel
from imaspy.imas_interface import LLInterfaceError, ll_interface
from imaspy.mdsplus_model import ensure_data_dir, mdsplus_model_dir
from imaspy.al_context import ALContext, LazyALContext
from imaspy.db_entry_helpers import _get_children, _delete_children, _put_children

logger = logging.getLogger(__name__)


class DBEntry:
    """Represents an IMAS database entry, which is a collection of stored IDSs."""

    _OPEN_MODES = {
        "r": OPEN_PULSE,
        "a": FORCE_OPEN_PULSE,
        "w": FORCE_CREATE_PULSE,
        "x": CREATE_PULSE,
    }

    @needs_imas
    def __legacy_init(
        self,
        backend_id: int,
        db_name: str,
        shot: int,
        run: int,
        user_name: Optional[str] = None,
        data_version: Optional[str] = None,
    ):
        self._legacy_init = True
        self.backend_id = backend_id
        self.db_name = db_name
        self.shot = shot
        self.run = run
        self.user_name = user_name or os.environ["USER"]
        self.data_version = data_version or os.environ.get("IMAS_VERSION", "")
        self.uri = None

    @needs_imas
    def __init__(
        self,
        uri: Optional[str] = None,
        mode: Optional[str] = None,
        *args,
        dd_version: Optional[str] = None,
        xml_path: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Create a new IMAS database entry object.

        You may use the optional arguments ``dd_version`` or ``xml_path`` to indicate
        the Data Dictionary version for usage with this Database Entry. If neither are
        supplied, the version is obtained from the IMAS_VERSION environment variable. If
        that also is not available, the latest available DD version is used.

        When using this DBEntry for reading data (:meth:`get` or :meth:`get_slice`), the
        returned IDSToplevel will be in the DD version specified. If the on-disk format
        is for a different DD version, the data is converted automatically.

        When using this DBEntry for writing data (:meth:`put` or :meth:`put_slice`), the
        specified DD version is used for writing to the backend. If the provided
        IDSToplevel is for a different DD version, the data is converted automatically.

        Args:
            uri: IMAS URI of the data source (only available when using Access Layer 5)
            mode: Mode to open the pulse in. One of:

              - ``"r"``: Open an existing data entry. Raises an error when the data
                entry does not exist.

                .. note:: The opened data entry is not read-only, it can be written to.
              - ``"a"``: Open an existing data entry, create the data entry if it does
                not exist.
              - ``"w"``: Create a data entry, overwriting any existing.

                .. caution:: This will irreversibly delete any existing data.
              - ``"x"``: Create a data entry. Raises an error when a data entry already
                exists.

        Notes:

            Instead of the URI and mode, legacy parameters can be supplied as well. When
            using Access Layer version 4, the URI/mode arguments are not supported and
            the legacy parameters must be used instead:

            ``backend_id``
                ID of the backend to use, e.g. HDF5_BACKEND. See :ref:`Backend
                identifiers`.

            ``db_name``
                Database name, e.g. "ITER".

            ``shot``
                Shot number of the database entry

            ``run``
                Run number of the database entry

            ``user_name``
                User name of the database, retrieved from environment when not supplied.

            ``data_version``
                Major version of the DD used by the the access layer, retrieved from
                environment when not supplied.

        Keyword Args:
            dd_version: Data dictionary version to use.
            xml_path: Data dictionary definition XML file to use.
        """
        self._db_ctx: Optional[ALContext] = None
        if args or kwargs:
            # uri and mode may be set as positional arguments in which case they
            # represent backend_id and db_name, though backend_id and/or db_name may
            # also be provided as kwargs
            if mode is not None:
                args = (uri, mode) + args
            elif uri is not None:
                args = (uri,) + args
            self.__legacy_init(*args, **kwargs)
        elif ll_interface._al_version.major < 5:
            raise ValueError("Providing a URI to DBEntry() requires IMAS version 5.")
        else:
            self._legacy_init = False
            if not uri:
                raise ValueError("No URI provided.")
            self.uri = uri
            if mode not in self._OPEN_MODES:
                modes = set(self._OPEN_MODES)
                raise ValueError(f"Unknown mode {mode!r}, was expecting any of {modes}")
            self.open(self._OPEN_MODES[mode])

        self._dd_version = dd_version
        self._xml_path = xml_path
        self._ids_factory = IDSFactory(dd_version, xml_path)
        self._uses_mdsplus = False

    def _build_legacy_uri(self, options):
        if not self._legacy_init:
            raise RuntimeError(
                "DBEntry was not constructed with legacy parameters, and no"
                " URI provided to 'open()' or 'create()'"
            )
        status, uri = ll_interface.build_uri_from_legacy_parameters(
            self.backend_id,
            self.shot,
            self.run,
            self.user_name,
            self.db_name,
            self.data_version,
            options if options is not None else "",
        )
        if status != 0:
            raise RuntimeError("Error calling al_build_uri_from_legacy_parameters()")
        return uri

    @property
    def factory(self) -> IDSFactory:
        """Get the IDS factory used by this DB entry."""
        return self._ids_factory

    @property
    def dd_version(self) -> str:
        """Get the DD version used by this DB entry"""
        return self._ids_factory.version

    def _open_pulse(self, mode: int, options: Any) -> None:
        """Internal method implementing open()/create()."""
        if self._db_ctx is not None:
            self.close()
        if self._legacy_init:
            if ll_interface._al_version.major < 5:
                # AL4 compatibility
                if self.backend_id == MDSPLUS_BACKEND:
                    self._setup_mdsplus()
                status, ctx = ll_interface.begin_pulse_action(
                    self.backend_id,
                    self.shot,
                    self.run,
                    self.user_name,
                    self.db_name,
                    self.data_version,
                )
                if status != 0:
                    raise RuntimeError(f"Error calling begin_pulse_action(), {status=}")
                status = ll_interface.open_pulse(ctx, mode, options)
            else:
                self.uri = self._build_legacy_uri(options)
        if ll_interface._al_version.major >= 5:
            if urlparse(self.uri).path.lower() == "mdsplus":
                self._setup_mdsplus()
            status, ctx = ll_interface.begin_dataentry_action(self.uri, mode)
        if status != 0:
            raise RuntimeError(f"Error opening/creating database entry: {status=}")
        self._db_ctx = ALContext(ctx)

    def _setup_mdsplus(self):
        """Additional setup required for MDSPLUS backend"""
        # Load the model directory of the IMAS version that we got instantiated with.
        # This does not cover the case of reading an idstoplevel and only then finding
        # out which version it is. But, I think that the model dir is not required if
        # there is an existing file.
        if self._dd_version or self._xml_path:
            ids_path = mdsplus_model_dir(
                version=self._dd_version, xml_file=self._xml_path
            )
        elif self._ids_factory._version:
            ids_path = mdsplus_model_dir(version=self._ids_factory._version)
        else:
            # This doesn't actually matter much, since if we are auto-loading
            # the backend version it is an existing file and we don't need
            # the model (I think). If we are not auto-loading then one of
            # the above two conditions should be true.
            logger.warning(
                "No backend version information available, not building MDSPlus model."
            )
            ids_path = None
        if ids_path:
            os.environ["ids_path"] = ids_path

        # Note: MDSPLUS model directory only uses the major version component of
        # IMAS_VERSION, so we'll take the first character of IMAS_VERSION, or fallback
        # to "3" (older we don't support, newer is not available and probably never will
        # with Access Layer 4.x).
        if ll_interface._al_version.major == 4:
            version = self._dd_version[0] if self._dd_version else "3"
            ensure_data_dir(str(self.user_name), self.db_name, version, self.run)
        self._uses_mdsplus = True

    def close(self, *, erase=False):
        """Close this Database Entry.

        Keyword Args:
            erase: Remove the pulse file from the database.
        """
        if self._db_ctx is None:
            return

        mode = ERASE_PULSE if erase else CLOSE_PULSE
        status = ll_interface.close_pulse(self._db_ctx.ctx, mode)
        if status != 0:
            raise RuntimeError(f"Error closing database entry: {status=}")

        ll_interface.end_action(self._db_ctx.ctx)
        self._db_ctx = None

    def create(self, *, options=None, force=True) -> None:
        """Create a new database entry.

        Caution:
            This method erases the previous entry if it existed!

        Keyword Args:
            options: Backend specific options.
            force: Whether to force create the database entry.

        Example:
            .. code-block:: python

                import imaspy

                imas_entry = imaspy.DBEntry(imaspy.ids_defs.HDF5_BACKEND, "test", 1, 1234)
                imas_entry.create()
        """  # noqa
        self._open_pulse(FORCE_CREATE_PULSE if force else CREATE_PULSE, options)

    def open(self, mode=OPEN_PULSE, *, options=None, force=False) -> None:
        """Open an existing database entry.

        Keyword Args:
            options: Backend specific options.
            force: Whether to force open the database entry.

        Example:
            .. code-block:: python

                import imaspy

                imas_entry = imaspy.DBEntry(imaspy.ids_defs.HDF5_BACKEND, "test", 1, 1234)
                imas_entry.open()
        """  # noqa
        if force:
            mode = FORCE_OPEN_PULSE
            logger.warning(
                "DBEntry.open(force=True) is deprecated, "
                "use DBEntry.open(FORCE_OPEN_PULSE) instead"
            )
        self._open_pulse(mode, options)

    def get(
        self,
        ids_name: str,
        occurrence: int = 0,
        *,
        lazy: bool = False,
        autoconvert: bool = True,
        destination: Optional[IDSToplevel] = None,
    ) -> IDSToplevel:
        """Read the contents of the an IDS into memory.

        This method fetches an IDS in its entirety, with all time slices it may contain.
        See :meth:`get_slice` for reading a specific time slice.

        Args:
            ids_name: Name of the IDS to read from the backend.
            occurrence: Which occurrence of the IDS to read.

        Keyword Args:
            lazy: When set to ``True``, values in this IDS will be retrieved only when
                needed (instead of getting the full IDS immediately). See :ref:`Lazy
                loading` for more details.

                .. note:: Lazy loading is not supported by the ASCII backend.
            autoconvert: Automatically convert IDSs.

                If enabled (default), a call to ``get()`` or ``get_slice()`` will return
                an IDS from the Data Dictionary version attached to this Data Entry.
                Data is automatically converted between the on-disk version and the
                in-memory version.

                When set to ``False``, the IDS will be returned in the DD version it was
                stored in.
            destination: Populate this IDSToplevel instead of creating an empty one.

        Returns:
            The loaded IDS.

        Example:
            .. code-block:: python

                import imaspy

                imas_entry = imaspy.DBEntry(imaspy.ids_defs.MDSPLUS_BACKEND, "ITER", 131024, 41, "public")
                imas_entry.open()
                core_profiles = imas_entry.get("core_profiles")
        """  # noqa
        return self._get(ids_name, occurrence, None, 0, destination, lazy, autoconvert)

    def get_slice(
        self,
        ids_name: str,
        time_requested: float,
        interpolation_method: int,
        occurrence: int = 0,
        *,
        lazy: bool = False,
        autoconvert: bool = True,
        destination: Optional[IDSToplevel] = None,
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

            occurrence: Which occurrence of the IDS to read.

        Keyword Args:
            lazy: When set to ``True``, values in this IDS will be retrieved only when
                needed (instead of getting the full IDS immediately). See :ref:`Lazy
                loading` for more details.
            autoconvert: Automatically convert IDSs.

                If enabled (default), a call to ``get()`` or ``get_slice()`` will return
                an IDS from the Data Dictionary version attached to this Data Entry.
                Data is automatically converted between the on-disk version and the
                in-memory version.

                When set to ``False``, the IDS will be returned in the DD version it was
                stored in.
            destination: Populate this IDSToplevel instead of creating an empty one.

        Returns:
            The loaded IDS.

        Example:
            .. code-block:: python

                import imaspy

                imas_entry = imaspy.DBEntry(imaspy.ids_defs.MDSPLUS_BACKEND, "ITER", 131024, 41, "public")
                imas_entry.open()
                core_profiles = imas_entry.get_slice("core_profiles", 370, imaspy.ids_defs.PREVIOUS_INTERP)
        """  # noqa
        return self._get(
            ids_name,
            occurrence,
            time_requested,
            interpolation_method,
            destination,
            lazy,
            autoconvert,
        )

    def _get(
        self,
        ids_name: str,
        occurrence: int,
        time_requested: Optional[float],
        interpolation_method: int,
        destination: Optional[IDSToplevel],
        lazy: bool,
        autoconvert: bool,
    ) -> IDSToplevel:
        """Actual implementation of get() and get_slice()"""
        if self._db_ctx is None:
            raise RuntimeError("Database entry is not opened, use open() first.")
        if lazy and self.backend_id == ASCII_BACKEND:
            raise RuntimeError("Lazy loading is not supported by the ASCII backend.")
        if lazy and destination:
            raise ValueError("Cannot supply a destination IDS when lazy loading.")

        ll_path = ids_name
        if occurrence != 0:
            ll_path += f"/{occurrence}"

        with self._db_ctx.global_action(ll_path, READ_OP) as read_ctx:
            time_mode = read_ctx.read_data(
                "ids_properties/homogeneous_time", "", INTEGER_DATA, 0
            )
            dd_version = read_ctx.read_data(
                "ids_properties/version_put/data_dictionary", "", CHAR_DATA, 1
            )
        if time_mode not in IDS_TIME_MODES:
            raise RuntimeError(
                f"Invalid Database Entry: Found invalid value '{time_mode}' for "
                "ids_properties.homogeneous_time in IDS "
                f"{ids_name}, occurrence {occurrence}."
            )

        if not dd_version:
            logger.warning(
                "Loaded IDS (%s, occurrence %s) does not specify a data dictionary "
                "version. Some data may not be loaded.",
                ids_name,
                occurrence,
            )
        # Ensure we have a destination
        if not destination:
            if autoconvert:  # store results in our DD version
                destination = self._ids_factory.new(ids_name, _lazy=lazy)
            else:  # store results in on-disk DD version
                destination = IDSFactory(dd_version).new(ids_name, _lazy=lazy)
        # Create a version conversion map, if needed
        nbc_map = None
        if dd_version and dd_version != destination._dd_version:
            ddmap, source_is_older = dd_version_map_from_factories(
                ids_name, IDSFactory(version=dd_version), self._ids_factory
            )
            nbc_map = ddmap.new_to_old if source_is_older else ddmap.old_to_new

        if lazy:
            context = LazyALContext(dbentry=self, nbc_map=nbc_map, time_mode=time_mode)
        else:
            context = self._db_ctx
        # Now fill the IDSToplevel
        if time_requested is None or destination.metadata.type is IDSType.CONSTANT:
            # called from get(), or when the IDS is constant (see IMAS-3330)
            manager = context.global_action(ll_path, READ_OP)
        else:  # get_slice
            manager = context.slice_action(
                ll_path, READ_OP, time_requested, interpolation_method
            )
        with manager as read_ctx:
            if lazy:
                destination._set_lazy_context(read_ctx)
            else:
                _get_children(destination, read_ctx, time_mode, nbc_map)

        return destination

    def put(self, ids: IDSToplevel, occurrence: int = 0) -> None:
        """Write the contents of an IDS into this Database Entry.

        The IDS is written entirely, with all time slices it may contain.

        Caution:
            The put method deletes any previously existing data within the target IDS
            occurrence in the Database Entry.

        Args:
            ids: IDS object to put.
            occurrence: Which occurrence of the IDS to write to.

        Example:
            .. code-block:: python

                ids = imaspy.IDSFactory().pf_active()
                ...  # fill the pf_active IDS here
                imas_entry.put(ids)
        """
        self._put(ids, occurrence, False)

    def put_slice(self, ids: IDSToplevel, occurrence: int = 0) -> None:
        """Append a time slice of the provided IDS to the Database Entry.

        Time slices must be appended in strictly increasing time order, since the Access
        Layer is not reordering time arrays. Doing otherwise will result in
        non-monotonic time arrays, which will create confusion and make subsequent
        :meth:`get_slice` commands to fail.

        Although being put progressively time slice by time slice, the final IDS must be
        compliant with the data dictionary. A typical error when constructing IDS
        variables time slice by time slice is to change the size of the IDS fields
        during the time loop, which is not allowed but for the children of an array of
        structure which has time as its coordinate.

        The :meth:`put_slice` command is appending data, so does not modify previously
        existing data within the target IDS occurrence in the Data Entry.

        It is possible possible to append several time slices to a node of the IDS in
        one :meth:`put_slice` call, however the user must ensure that the size of the
        time dimension of the node remains consistent with the size of its timebase.

        Args:
            ids: IDS object to put.
            occurrence: Which occurrence of the IDS to write to.

        Example:
            A frequent use case is storing IMAS data progressively in a time loop. You
            can fill the constant and static values only once and progressively append
            the dynamic values calculated in each step of the time loop with
            :meth:`put_slice`.

            .. code-block:: python

                ids = imaspy.IDSFactory().pf_active() ...  # fill the static data of the
                pf_active IDS here for i in range(N):
                    ... # fill time slice of the pf_active IDS imas_entry.put_slice(ids)
        """
        self._put(ids, occurrence, True)

    def _put(self, ids: IDSToplevel, occurrence: int, is_slice: bool):
        """Actual implementation of put() and put_slice()"""
        if self._db_ctx is None:
            raise RuntimeError("Database entry is not opened, use open() first.")
        if ids._lazy:
            raise ValueError("Lazy loaded IDSs cannot be used in put or put_slice.")

        # Automatic validation
        disable_validate = os.environ.get("IMAS_AL_DISABLE_VALIDATE")
        if not disable_validate or disable_validate == "0":
            try:
                ids.validate()
            except ValidationError:
                logger.error(
                    "IDS %s is not valid. You can disable automatic IDS validation by "
                    "setting the environment variable IMAS_AL_DISABLE_VALIDATE=1.",
                    ids.metadata.name,
                )
                raise

        ids_name = ids.metadata.name
        # Create a version conversion map, if needed
        nbc_map = None
        if ids._version != self._ids_factory._version:
            ddmap, source_is_older = dd_version_map_from_factories(
                ids_name, ids._parent, self._ids_factory
            )
            nbc_map = ddmap.old_to_new if source_is_older else ddmap.new_to_old

        # Verify homogeneous_time is set
        time_mode = ids.ids_properties.homogeneous_time
        # TODO: allow unset homogeneous_time and quit with no action?
        if time_mode not in IDS_TIME_MODES:
            raise ValueError("'ids_properties.homogeneous_time' is not set or invalid.")
        # IMAS-3330: automatically set time mode to independent:
        if ids.metadata.type is IDSType.CONSTANT:
            if time_mode != IDS_TIME_MODE_INDEPENDENT:
                logger.warning(
                    "ids_properties/homogeneous_time has been set to 2 for the constant"
                    " IDS %s/%d. Please check the program which has filled this IDS"
                    " since this is the mandatory value for a constant IDS",
                    ids_name,
                    occurrence,
                )
                ids.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
        if is_slice and time_mode == IDS_TIME_MODE_INDEPENDENT:
            raise RuntimeError("Cannot use put_slice with IDS_TIME_MODE_INDEPENDENT.")

        ll_path = ids_name
        if occurrence != 0:
            ll_path += f"/{occurrence}"

        # Set version_put properties (version_put was added in DD 3.22)
        if hasattr(ids.ids_properties, "version_put"):
            version_put = ids.ids_properties.version_put
            version_put.data_dictionary = self._ids_factory._version
            version_put.access_layer = ll_interface._al_version_str
            version_put.access_layer_language = "imaspy " + imaspy.__version__

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
                # New IDS to ensure all fields in "our" DD version are deleted
                # If ids is in another version, we might not erase all fields
                _delete_children(self._ids_factory.new(ids_name).metadata, write_ctx)

        if is_slice:
            manager = self._db_ctx.slice_action(
                ll_path, WRITE_OP, UNDEFINED_TIME, UNDEFINED_INTERP
            )
        else:
            manager = self._db_ctx.global_action(ll_path, WRITE_OP)
        verify_maxoccur = self._uses_mdsplus
        with manager as write_ctx:
            _put_children(ids, write_ctx, time_mode, is_slice, nbc_map, verify_maxoccur)

    def delete_data(self, ids_name: str, occurrence: int = 0) -> None:
        """Delete the provided IDS occurrence from this IMAS database entry.

        Args:
            ids_name: Name of the IDS to delete from the backend.
            occurrence: Which occurrence of the IDS to delete.
        """
        if self._db_ctx is None:
            raise RuntimeError("Database entry is not opened, use open() first.")
        ll_path = ids_name
        if occurrence != 0:
            ll_path += f"/{occurrence}"
        ids = self._ids_factory.new(ids_name)
        with self._db_ctx.global_action(ll_path, WRITE_OP) as write_ctx:
            _delete_children(ids.metadata, write_ctx, "")

    @overload
    def list_all_occurrences(self, ids_name: str, node_path: None = None) -> List[int]:
        ...

    @overload
    def list_all_occurrences(
        self, ids_name: str, node_path: str
    ) -> Tuple[List[int], List[IDSMixin]]:
        ...

    def list_all_occurrences(self, ids_name, node_path=None):
        """List all non-empty occurrences of an IDS

        When using AL 5.1 or later, this will request the occurrences from the backend.
        In earlier versions of the Access Layer, IMASPy will attempt to determine which
        occurrences are filled.

        Args:
            ids_name: name of the IDS (e.g. "magnetics", "core_profiles" or
                "equilibrium")
            node_path: path to a Data-Dictionary node (e.g. "ids_properties/comment",
                "code/name", "ids_properties/provider").

        Returns:
            tuple or list:
                When no ``node_path`` is supplied, a (sorted) list with non-empty
                occurrence numbers is returned.

                When ``node_path`` is supplied, a tuple ``(occurrence_list,
                node_content_list)`` is returned. The ``occurrence_list`` is a (sorted)
                list of non-empty occurrence numbers. The ``node_content_list`` contains
                the contents of the node in the corresponding occurrences.

        Example:
            .. code-block:: python

                dbentry = imas.DBEntry(uri, "r")
                occurrence_list, node_content_list = \\
                    dbentry.list_all_occurrences("magnetics", "ids_properties/comment")
                dbentry.close()
        """
        if self._db_ctx is None:
            raise RuntimeError("Database entry is not opened, use open() first.")

        try:
            occurrence_list = list(ll_interface.get_occurrences(self._db_ctx, ids_name))
        except LLInterfaceError:
            # al_get_occurrences is not available in the lowlevel
            raise RuntimeError(
                "list_all_occurrences is not available. "
                "Access Layer 5.1 or newer is required."
            ) from None

        if node_path is None:
            return occurrence_list

        node_content_list = [
            self.get(ids_name, occ, lazy=True)[node_path] for occ in occurrence_list
        ]
        return occurrence_list, node_content_list
