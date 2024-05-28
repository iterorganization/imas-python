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
4.  It should be possible to store any valid IDS (according to the Data
    Dictionary) in an IMAS netCDF file. 


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

These conventions require functionality that is only available in the netCDF-4
file format. As a result, this is the only supported file format for IMAS netCDF
files.


Global attributes
-----------------

The following global (file-level) attributes should be set in IMAS netCDF files:

``Conventions``
    The ``Conventions`` attribute is set to "``IMAS``" to indicate that the file
    follows these IMAS conventions.

``data_dictionary_version``
    The ``data_dictionary_version`` attribute is set to the version string of
    the Data Dictionary it follows. For example: "``3.38.1``", "``3.41.0``".


Groups
------

The IMAS Data Dictionary organizes data in Interface Data Structures (IDS). The
IMAS Access Layer stores collections of IDSs in a Data Entry. Multiple
*occurrences* of an IDS can occur in a Data Entry.

This same structure is mirrored in IMAS netCDF files, using netCDF groups. All
data inside an IDS structure is stored as variables in the netCDF group "``{IDS
name}/{occurrence}/``". ``IDS name`` represents the name of the IDS, such as
``core_profiles``, ``pf_active``, etc. ``occurrence`` is an integer ``>= 0``
indicating the occurrence number of the IDS. When only one occurrence of the IDS
is stored in the netCDF file, the occurrence is typically ``0``.

.. code-block:: text
    :caption: Example group structure for an IDS

    /core_profiles/0
    /pf_active/0
    /pf_active/1
    /summary/0

Each IDS/occurrence is stored independently. There are no shared variables or
dimensions.


Variables
---------

Variable names
''''''''''''''

NetCDF variable names are derived from the Data Dictionary node names by taking
it's path and replacing the forward slashes (``/``) by periods (``.``). For
example, the netCDF variable name for ``profiles_1d/ion/temperature`` in the
``core_profiles`` IDS is ``profiles_1d.ion.temperature``.


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

The following attributes can be present on the netCDF variables:

``_FillValue``
    The ``_FillValue`` attribute specifies the fill value used to pre-fill disk
    space allocated to the variable.

    It is recommended to use the default netCDF fill values: ``-2,147,483,647``
    for integers, ``9.969209968386869e+36`` for floating point data and the
    empty string ``""`` for string data.

    .. seealso:: https://docs.unidata.ucar.edu/netcdf-c/current/attribute_conventions.html

``ancillary_variables``
    The IMAS Data Dictionary allows error bar nodes (ending in ``_error_upper``,
    ``_error_lower``) for many quantities. When these error nodes are filled, it
    is recommended to fill the ``ancillary_variables`` attribute with the names
    of the error bar variables.

    .. seealso:: https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html#ancillary-data

``coordinates``
    The ``coordinates`` attribute contains a *blank separated list of the names
    of auxiliary coordinate variables*. There is no restriction on the order in
    which the auxiliary variables appear.

    See the :ref:`Dimensions and auxiliary coordinates` section on how to
    determine auxiliary coordinates from the Data Model defined by the IMAS Data
    Dictionary.

    .. seealso:: https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html#coordinate-system

``documentation``
    The ``documentation`` attribute contains a documentation string for the
    variable. This documentation should correspond to the documentation string
    defined by the IMAS Data Dictionary.

``sparse``
    When the ``sparse`` attribute is present, it indicates that the data in this
    variable does not span the full size of its dimensions. The value of this
    attribute should be a human-readable string indicating that not all values
    are filled.

    See the :ref:`Tensorization` section for more information and examples for
    the ``sparse`` attribute and handling data that does not span the full size
    of its dimensions.

``units``
    A string indicating the units used for the variable's data. *Units* are
    defined by the IMAS Data Dictionary and applications must follow this.

    .. note::

        The IMAS Data Dictionary units currently don't always adhere to the
        `UDUNITS <https://docs.unidata.ucar.edu/udunits/current/>`__ conventions.
        Tracker `IMAS-5246 <https://jira.iter.org/browse/IMAS-5246>`__ was
        created for this.

    .. seealso:: https://docs.unidata.ucar.edu/netcdf-c/current/attribute_conventions.html


IDS metadata and provenance
===========================

TODO


.. _`Dimensions and auxiliary coordinates`:

Dimensions and auxiliary coordinates
====================================

NetCDF dimensions and :term:`auxiliary coordinate variable`\ s are derived from
the coordinate metadata stored in the IMAS Data Dictionary.

.. list-table::
    :header-rows: 1
    
    - * Data Dictionary Coordinate
      * Interpretation
      * NetCDF implications
    - * ``1...N``
      * There is no coordinate for this node, there is no limit on size.
      * Independent dimension.
    - * ``1...i``, with ``i=1,2,3,...``
      * There is no coordinate for this node, size must be exactly ``i`` or 0.
      * Independent dimension.
    - * ``1...N`` (same as ``x/y/z``)
      * There is no coordinate, but this node must have the same size as node ``x/y/z``.
      * Shared dimension with variable ``x.y.z``, ``x.y.z`` is **not** an auxiliary coordinate.
    - * ``x/y/z``
      * Node ``x/y/z`` is the coordinate for this node.
      * Shared dimension with variable ``x.y.z``, ``x.y.z`` can be an auxiliary coordinate.
    - * ``u/v/w OR x/y/z``
      * Either node ``u/v/w`` or node ``x/y/z`` must be filled and it is the coordinate for this node.
      * Shared dimension with variables ``u.v.w`` and ``x.y.z``. Both ``u.v.w`` and ``x.y.z`` can be auxiliary coordinates.
    - * ``x/y/z OR 1...1``
      * Either node ``x/y/z`` is the coordinate for this node, or this node must have size 1.
      * Shared dimension with variable ``x.y.z`` [#or1]_, ``x.y.z`` can be an auxiliary coordinate.
    - * ``1...N`` (same as ``x/y/z OR 1...1``)
      * There is no coordinate for this node, but this node must either have the same size as node ``x/y/z`` or have size 1.
      * Shared dimension with variable ``x.y.z`` [#or1]_, ``x.y.z`` is **not** an auxiliary coordinate.

.. [#or1] Even though a dummy, size=1, dimension could be used if the data
    stored in the node is never exceeding 1 element, this decision was made to
    allow determining dimension names without having to inspect the data stored.


Time dimensions
---------------

The IMAS Data Dictionary provides for three different time modes. The special
integer variable ``ids_properties.homogeneous_time`` indicates which of the time
mode an IDS is using:

- Heterogeneous time mode (``ids_properties.homogeneous_time = 0``), multiple
  time dimensions may exist in the IDS.
- Homogeneous time mode (``ids_properties.homogeneous_time = 1``), there is only
  a single time coordinate, which is stored in the ``time`` :term:`coordinate
  variable`.
- Time independent mode (``ids_properties.homogeneous_time = 2``) means that
  there is no time-varying data in this IDS and only variables that don't have a
  time dimension may be stored.

The selected time mode impacts which :term:`time dimension` is used, see below
table for some examples.

.. list-table::
    :header-rows: 1

    * - Example Data Dictionary node
      - Data Dictionary time coordinate
      - Time dimension (heterogeneous mode)
      - Time dimension (homogeneous mode)
    * - ``global_quantities/ip`` (``core_profiles`` IDS)
      - ``time``
      - ``time``
      - ``time``
    * - ``coil/current/data`` (``pf_active`` IDS)
      - ``coil(i1)/current/time``
      - ``coil.current.time``
      - ``time``
    * - ``time_slice`` (``equilibrium`` IDS) [#aos]_
      - ``time_slice(itime)/time``
      - ``time_slice.time``
      - ``time``

.. [#aos] This is an Array of Structures and not a data variable. See the
    :ref:`Tensorization` section for more information on Arrays of Structures.


Additional auxiliary coordinates
--------------------------------

TODO AOS/name/label/identifier


.. _`Tensorization`:

Tensorization
=============

TODO describe tensorization
