IMAS netCDF files
=================

.. toctree::
    :hidden:

    netcdf/conventions


IMASPy supports reading IDSs from and writing IDSs to IMAS netCDF files. This
feature is currently in alpha status, and its functionality may change in
upcoming minor releases of IMASPy.

A detailed description of the IMAS netCDF format and conventions can be found on
the :ref:`IMAS conventions for the netCDF data format` page.

Reading from and writing to netCDF files uses the same :py:class:`imaspy.DBEntry
<imaspy.db_entry.DBEntry>` API as reading and writing to Access Layer backends.
If you provide a path to a netCDF file (ending with ``.nc``) the netCDF backend
will be used for :py:meth:`~imaspy.db_entry.DBEntry.get` and
:py:meth:`~imaspy.db_entry.DBEntry.put` calls. See the below example:

.. code-block:: python
    :caption: Use DBEntry to write and read IMAS netCDF files

    import imaspy

    cp = imaspy.IDSFactory().core_profiles()
    cp.ids_properties.homogeneous_time = imaspy.ids_defs.IDS_TIME_MODE_INDEPENDENT
    cp.ids_properties.comment = "Test IDS"

    # This will create the `test.nc` file and stores the core_profiles IDS in it
    with imaspy.DBEntry("test.nc", "w") as netcdf_entry:
        netcdf_entry.put(cp)

    # Reading back:
    with imaspy.DBEntry("test.nc", "r") as netcdf_entry:
        cp2 = netcdf_entry.get("core_profiles")

    imaspy.util.print_tree(cp2)
