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

The preliminary IMASPy API for dealing with IMAS netCDF files can be found in
:py:mod:`imaspy.netcdf`. The :py:class:`imaspy.netcdf.nc_entry.NCEntry` class is
intended as main user-facing API.
