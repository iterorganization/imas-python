===========================================
IMAS conventions for the netCDF data format
===========================================

This page describes the conventions for storing `IMAS
<https://imas.iter.org/>`__ data in the netCDF4 data format. These conventions
build on top of the conventions described in the `NetCDF User Guide (NUG)
<https://docs.unidata.ucar.edu/nug/current/index.html>`__ and borrow as much as
possible from the `Climate and Forecast (CF) conventions
<https://cfconventions.org/>`__.


Introduction
============

Goals
-----

The netCDF library is a cross-platform library that enables to read and write
*self-describing* datasets consisting of multi-dimensional arrays. The purpose
of these IMAS conventions is to define how to store IMAS data, conforming to the
`IMAS Data Dictionary <https://confluence.iter.org/display/IMP/Data+Model>`__,
in a netCDF file.


Principles for design
---------------------

The following principles are followed in the design of these conventions:

1.  The data model described by the IMAS Data Dictionary is leading.
2.  The data should be self-describing without needing to access the Data
    Dictionary documentation. All relevant metadata should be available in the
    netCDF file.
3.  Widely used conventions, like the Climate and Forecast conventions, should
    be used as much as possible.


Terminology
-----------

The terms in this document that refer to components of a netCDF file are defined
in the NetCDF User's Guide (NUG) and/or the CF Conventions. Some of those
definitions are repeated below for convenience.

.. glossary::

    auxiliary coordinate variable
        Any netCDF variable that contains coordinate data, but is not a
        coordinate variable (in the sense of that term defined by the NUG and
        used by this standard -- see below). Unlike coordinate variables, there
        is no relationship between the name of an auxiliary coordinate variable
        and the name(s) of its dimension(s).

        .. seealso:: https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html#terminology

    coordinate variable
        We use this term precisely as it is defined in the `NUG section on
        coordinate variables
        <https://docs.unidata.ucar.edu/nug/current/best_practices.html#bp_Coordinate-Systems>`__.
        It is a one-dimensional variable with the same name as its dimension
        [e.g., ``time(time)``], and it is defined as a numeric data type with
        values in strict monotonic order (all values are different, and they are
        arranged in either consistently increasing or consistently decreasing
        order). Missing values are not allowed in coordinate variables.

        .. seealso:: https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html#terminology

    multi-dimensional coordinate variable
        An :term:`auxiliary coordinate variable` that is multidimensional.

        .. seealso:: https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html#terminology


    time dimension
        A dimension of a netCDF variable that has an associated time coordinate variable.

        .. seealso:: https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html#terminology


NetCDF files and components
===========================

In this section we describe conventions associated with filenames and the basic
comopnents of a netCDF file.


Filename
--------

NetCDF files should have the file name extension "``.nc``".


File format
-----------

These conventions make heavy use of functionality that is only available in the
netCDF-4 file format. As a result, this is the only supported file format for
IMAS netCDF files.


Global attributes
-----------------

The following global (file-level) attributes should be set in IMAS netCDF files:

``Conventions``
    The ``Conventions`` attribute is set to "``IMAS``" to indicate that the file
    follows these IMAS conventions.

``data_dictionary_version``
    The ``data_dictionary_version`` attribute is set to the version string of
    the Data Dictionary it follows. Some examples: "``3.38.1``", "``3.41.0``".


Groups
------

The IMAS Data Dictionary organizes data in Interface Data Structures (IDS). The
IMAS Access Layer stores collections of IDSs in a Data Entry. Multiple
*occurrences* of an IDS can occur in a Data Entry.

This same structure is mirrored in IMAS netCDF files, using netCDF groups. All
data inside an IDS structure is stored as variables in the netCDF group ``{IDS
name}/{occurrence}/``. ``IDS name`` represents the name of the IDS, such as
``core_profiles``, ``pf_active``, etc. ``occurrence`` is an integer ``>= 0``
indicating the occurrence number of the IDS. When only one occurrence of the IDS
is stored in the netCDF file, the occurrence is typically ``0``.

.. code-block:: text
    :caption: Example group structure for an IDS

    /core_profiles/0
    /pf_active/0
    /pf_active/1
    /summary/0

The data of each IDS/occurrence is stored independently of eachother. There are
no shared variables or dimensions.


Variables
---------

Variable names
''''''''''''''

NetCDF variable names are 


Data Types
''''''''''

Data types of variables are defined by the IMAS Data Dictionary:

- ``STR_*``: strings are represented in the netCDF file with the ``string`` data
  type.
- ``INT_*``: integer numbers are represented in the netCDF file with the ``int``
  (32-bits signed integer) data type.
- ``FLT_*``: floating point numbers are represented in the netCDF file with the
  ``double`` (64-bits floating point) data type.
- ``CPX_*``: complex numbers are represented in the netCDF file using a compound
  data type with an ``r`` (for the real-valued) and ``i`` (for the
  imaginary-valued) component. See the `nc-complex
  <https://nc-complex.readthedocs.io/en/latest/>`__ package for further details.

The IMAS Data Dictionary also defines Structures and Arrays of Structures. They
don't contain data themselves, but can be stored as variables in the netCDF file
to attach metadata (such as documentation) to.


Variable attributes
'''''''''''''''''''




Tensorization
=============
