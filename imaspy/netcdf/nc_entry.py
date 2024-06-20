# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""NetCDF IO support for IMASPy. Requires [netcdf] extra dependencies.
"""

import logging
import os
from typing import Optional

from netCDF4 import Dataset

import imaspy
from imaspy.ids_convert import convert_ids
from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, IDS_TIME_MODES
from imaspy.ids_factory import IDSFactory
from imaspy.ids_metadata import IDSType
from imaspy.ids_toplevel import IDSToplevel
from imaspy.netcdf.ids2nc import IDS2NC
from imaspy.netcdf.nc2ids import nc2ids

logger = logging.getLogger(__name__)


class NCEntry:
    """:class:`imaspy.db_entry.DBEntry` analogue for IMAS netCDF files."""

    def __init__(
        self,
        filename: str,
        mode: str,
        dd_version: Optional[str] = None,
        xml_path: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Open a netCDF dataset for reading or writing.

        Args:
            filename: Name of the netCDF file to hold the dataset.
            mode: Access mode, options:

                *   ``r``: open file for read-only
                *   ``w``: open file for writing, overwrites any existing file
                *   ``x``: open file for writing, fails if the file exists
                *   ``a``/``r+``: open file for appending

        Keyword Args:
            dd_version: Data dictionary version to use.
            xml_path: Data dictionary definition XML file to use.

        Additional keyword arguments are passed on to the ``netCDF4.Dataset``
        constructor.
        """
        self._dd_version = dd_version
        self._xml_path = xml_path
        self._ids_factory = IDSFactory(dd_version, xml_path)

        kwargs = {"auto_complex": True, **kwargs, "format": "NETCDF4"}
        self._dataset = Dataset(filename, mode, **kwargs)

        if self._dataset.dimensions or self._dataset.variables or self._dataset.groups:
            if "data_dictionary_version" not in self._dataset.ncattrs():
                raise RuntimeError(
                    "Invalid netCDF file: `data_dictionary_version` missing"
                )
            dataset_dd_version = self._dataset.data_dictionary_version
            if dataset_dd_version == self.dd_version:
                self._dataset_ids_factory = self._ids_factory
            else:
                self._dataset_ids_factory = IDSFactory(dataset_dd_version)
            # TODO: check if this is a valid IMAS netCDF file

        else:
            # Looks like this is an empty file, let's set global attributes
            self._dataset_ids_factory = self._ids_factory
            self._dataset.Conventions = "IMAS"
            self._dataset.data_dictionary_version = self._ids_factory.dd_version

    def __enter__(self):
        # Context manager protocol
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Context manager protocol
        self.close()

    @property
    def factory(self) -> IDSFactory:
        """Get the IDS factory used by this DB entry."""
        return self._ids_factory

    @property
    def dd_version(self) -> str:
        """Get the DD version used by this DB entry."""
        return self._ids_factory.version

    def close(self) -> None:
        """Close the underlying netCDF file."""
        self._dataset.close()

    def get(
        self,
        ids_name: str,
        occurrence: int = 0,
        *,
        lazy: bool = False,
        autoconvert: bool = True,
    ) -> IDSToplevel:
        """Read the contents of an IDS into memory.

        This method constructs an IDS and fills it with the data stored in the netCDF
        file.

        Args:
            ids_name: Name of the IDS to read from the backend.
            occurrence: Which occurrence of the IDS to read.

        Keyword Args:
            lazy: FIXME: not implemented yet
            autoconvert: Automatically convert IDSs.

                If enabled (default), a call to ``get()`` will return an IDS from the
                Data Dictionary version attached to this Data Entry. Data is
                automatically converted between the on-disk version and the in-memory
                version.

                When set to ``False``, the IDS will be returned in the DD version it was
                stored in.

        Returns:
            The loaded IDS.

        Example:
            .. code-block:: python

                nc_entry = NCEntry("path/to/data.nc", "r")
                core_profiles = nc_entry.get("core_profiles")
        """
        if lazy:
            raise NotImplementedError("Lazy loading is not yet implemented")
        ids = self._dataset_ids_factory.new(ids_name)
        group = self._dataset[f"{ids_name}/{occurrence}"]
        nc2ids(group, ids)

        if autoconvert and self._ids_factory is not self._dataset_ids_factory:
            return convert_ids(ids, factory=self._ids_factory)
        return ids

    def put(self, ids: IDSToplevel, occurrence: int = 0) -> None:
        """Write the contents of an IDS into this netCDF file.

        Args:
            ids: IDS object to put.
            occurrence: Which occurrence of the IDS to write to.

        Example:
            .. code-block:: python

                ids = imaspy.IDSFactory().pf_active()
                ...  # fill the pf_active IDS here
                nc_entry.put(ids)
        """
        ids_name = ids.metadata.name
        # netCDF4 limitation: cannot overwrite existing groups
        if ids_name in self._dataset.groups:
            if str(occurrence) in self._dataset[ids_name].groups:
                raise RuntimeError(
                    "Existing data exists for {ids_name}, occurrence {occurrence}."
                )
        group = self._dataset.createGroup(f"{ids_name}/{occurrence}")

        # FIXME: refactor the following code which is shared with DBEntry._put
        # Automatic validation
        disable_validate = os.environ.get("IMAS_AL_DISABLE_VALIDATE")
        if not disable_validate or disable_validate == "0":
            ids.validate()

        # TODO: conversion?
        assert ids._dd_version == self._dataset_ids_factory.dd_version

        # Verify homogeneous_time is set
        time_mode = ids.ids_properties.homogeneous_time
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

        # Set version_put properties (version_put was added in DD 3.22)
        if hasattr(ids.ids_properties, "version_put"):
            version_put = ids.ids_properties.version_put
            version_put.data_dictionary = self._ids_factory._version
            version_put.access_layer_language = "imaspy " + imaspy.__version__

        IDS2NC(ids, group).run()

    def list_all_occurrences(self, ids_name, node_path=None):
        """List all non-empty occurrences of an IDS

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

                occurrence_list = entry.list_all_occurrences("magnetics")
        """
        occurrence_list = []
        if ids_name in self._dataset.groups:
            for group in self._dataset[ids_name].groups:
                try:
                    occurrence_list.append(int(group))
                except ValueError:
                    pass  # ignore non-numerical groups
            occurrence_list.sort()

        if node_path is None:
            return occurrence_list

        variable_name = node_path.replace("/", ".")
        node_content_list = []
        for occurrence in occurrence_list:
            group = self._dataset[f"{ids_name}/{occurrence}"]
            if variable_name in group.variables():
                node_content_list.append(group[variable_name][()])
            else:
                node_content_list.append(None)
