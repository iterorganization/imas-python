IDS metadata
============

Besides the data structure, the IMAS Data Dictionary also defines metadata
associated with elements in the IDS, such as coordinate information, units, etc.
IMASPy provides the :py:class:`~imaspy.ids_metadata.IDSMetadata` API for
interacting with this metadata.

On this page you find several examples for querying and using the metadata of
IDS elements.

.. contents:: Contents
    :local:


Using coordinates of quantities
-------------------------------

All multi-dimensional quantities in an IDS have coordinate information. These
can be data nodes (for example 2D floating point data) or array of structure
nodes.


Get coordinate values
'''''''''''''''''''''

Each data node and array of structures has a ``coordinates`` attribute. By
indexing this attribute, you can retrieve the coordinate values for that
dimension. For example, ``coordinates[2]`` attempts to retrieve the coordinate
values for the third dimension of the data.

When another quantity in the IDS is used as a coordinate, that quantity is
looked up. See below example.

.. code-block:: python
    :caption: Example getting coordinate values belonging to a 1D quantity
    
    >>> root = imaspy.ids_root.IDSRoot()
    >>> root.core_profiles.profiles_1d.resize(1)
    >>> profile = root.core_profiles.profiles_1d[0]
    >>> profile.grid.rho_tor_norm = [0, 0.15, 0.3, 0.45, 0.6]
    >>> # Electron temperature has rho_tor_norm as coordinate:
    >>> profile.electrons.temperature.coordinates[0]
    IDSNumericArray("/core_profiles/profiles_1d/1/grid/rho_tor_norm", array([0.  , 0.15, 0.3 , 0.45, 0.6 ]))

When a coordinate is just an index, IMASPy generates a
:external:py:func:`numpy.arange` with the same length as the data. See below
example.

.. code-block:: python
    :caption: Example getting index coordinate values belonging to an array of structures

    >>> root = imaspy.ids_root.IDSRoot()
    >>> root.pf_active.coil.resize(10)
    >>> # Coordinate1 of coil is an index 1...N
    >>> root.pf_active.coil.coordinates[0]
    array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

.. rubric:: Time coordinates

Time coordinates are a special case: the coordinates depend on whether the IDS
is in homogeneous time mode or not. IMASPy handles this transparently.

.. code-block:: python
    :caption: Example getting time coordinate values

    >>> root = imaspy.ids_root.IDSRoot()
    >>> # profiles_1d is a time-dependent array of structures:
    >>> root.core_profiles.profiles_1d.coordinates[0]
    [...]
    ValueError: Invalid IDS time mode: ids_properties/homogeneous_time is -999999999, was expecting 0 or 1.
    >>> root.core_profiles.ids_properties.homogeneous_time = \\
    ...     imaspy.ids_defs.IDS_TIME_MODE_HOMOGENEOUS
    >>> # In homogeneous time mode, the root /time array is used
    >>> root.core_profiles.time = [0, 1]
    >>> root.core_profiles.profiles_1d.resize(2)
    >>> root.core_profiles.profiles_1d.coordinates[0]
    IDSNumericArray("/core_profiles/time", array([0., 1.]))
    >>> # But in heterogeneous time mode, profiles_1d/time is used instead
    >>> root.core_profiles.ids_properties.homogeneous_time = \\
    ...     imaspy.ids_defs.IDS_TIME_MODE_HETEROGENEOUS
    >>> root.core_profiles.profiles_1d.coordinates[0]
    array([-9.e+40, -9.e+40])

.. rubric:: Alternative coordinates

Sometimes the Data Dictionary indicates that multiple other quantities could be
used as a coordinate. For example, the
``distribution(i1)/profiles_2d(itime)/density(:,:)`` quantity in the
``distributions`` IDS has as first coordinate
``distribution(i1)/profiles_2d(itime)/grid/r OR
distribution(i1)/profiles_2d(itime)/grid/rho_tor_norm``. This means that either
``r`` or ``rho_tor_norm`` can be used as coordinate. When requesting such a
coordinate from IMASPy, four things may happen:

1.  When ``r`` is empty and ``rho_tor_norm`` not, ``coordinates[0]`` will return
    ``rho_tor_norm``.
2.  When ``rho_tor_norm`` is empty and ``r`` not, ``coordinates[0]`` will return
    ``r``.
3.  When both ``r`` and ``rho_tor_norm`` are not empty, IMASPy raises an error
    because it cannot determine which of the two coordinates should be used.
4.  Similarly, an error is raised by IMASPy when neither ``r`` nor
    ``rho_tor_norm`` are set.


.. seealso::
    API documentation for :py:class:`~imaspy.ids_coordinates.IDSCoordinates`


Other useful metadata
'''''''''''''''''''''

A brief overview of useful metadata attributes follows below.
Note that some attributes may not be set, this usually indicates that that
metadata attribute is not specified by the Data Dictionary.

data_type
    The data type of the IDS element. This is an instance of
    :py:class:`~imaspy.ids_data_type.IDSDataType`.

ndim
    The number of dimensions of the IDS element. A structure node always has 0
    dimensions. An array of structure node has 1 dimension. For data nodes
    the dimensionality can be between 0 and 6.

documentation
    A short description of the IDS element and (usually) its physical
    interpretation.

units
    The units for this quantity.

maxoccur
    The maximum number of times that this array of structures may appear for the
    MDSPLUS backend.


Query coordinate information
''''''''''''''''''''''''''''

In IMASPy you can query coordinate information in two ways:

1.  Directly query the coordinate attribute on the metadata:
    :code:`<quantity>.metadata.coordinate2` gives you the coordinate information
    for the second dimension of the quantity.
2.  Use the :py:attr:`IDSMetadata.coordinates` attribute:
    :code:`<quantity>.metadata.coordinates` is a tuple containing all coordinate
    information for the quantity.

The coordinate information from the Data Dictionary is parsed and stored in an
:py:class:`~imaspy.ids_coordinates.IDSCoordinate`. The Data Dictionary has
several types of coordinate information:

1.  When the coordinate is an index, the Data Dictionary indicates this via
    ``1...N``. When a literal ``N`` is given, no restrictions apply.
    
    It is also possible to have a specific value for ``N``, for example
    ``1...3``. Then, this dimension can contain at most 3 items.
2.  When another quantity in the IDS is used as a coordinate, the coordinate
    indicates the path to that other quantity.

.. TODO::
    Detailed coordinate descriptions should happen in the DD docs. Link to that
    when available.

.. code-block:: python
    :caption: Examples querying coordinate information

    >>> root = imaspy.ids_root.IDSRoot()
    >>> # coordinate1 of pf_active/coil is an index (the number of the coil)
    >>> root.pf_active.coil.metadata.coordinate1
    IDSCoordinate('1...N')
    >>> root.pf_active.coil.resize(1)
    >>> # pf_active/coil/current_limit_max is 2D, so has two coordinates
    >>> # Both refer to another quantity in the IDS
    >>> root.pf_active.coil[0].current_limit_max.metadata.coordinates
    (IDSCoordinate('coil(i1)/b_field_max'), IDSCoordinate('coil(i1)/temperature'))

.. seealso::
    API documentation for :py:class:`~imaspy.ids_coordinates.IDSCoordinate`.


Show all metadata associated to a quantity or structure
-------------------------------------------------------

Not all metadata from the IMAS Data Dictionary is handled specially by IMASPy.
This metadata is still accessible on the :code:`metadata` attribute. You can use
:external:py:func:`vars` to get an overview of all metadata associated to an
element in an IDS.

.. code-block:: python
    :caption: Example showing all metadata for some ``core_profiles`` elements.

    >>> from pprint import pprint
    >>> root = imaspy.ids_root.IDSRoot()
    >>> pprint(vars(root.core_profiles.ids_properties.metadata))
    {'_init_done': True,
     'coordinates': (),
     'coordinates_same_as': (),
     'data_type': <IDSDataType.STRUCTURE: 'structure'>,
     'documentation': 'Interface Data Structure properties. This element '
                      'identifies the node above as an IDS',
     'maxoccur': None,
     'name': 'ids_properties',
     'ndim': 0,
     'path': IDSPath('ids_properties'),
     'path_doc': 'ids_properties',
     'structure_reference': 'ids_properties'}
    >>> pprint(vars(root.core_profiles.time.metadata))
    {'_init_done': True,
     'coordinate1': IDSCoordinate('1...N'),
     'coordinates': (IDSCoordinate('1...N'),),
     'coordinates_same_as': (IDSCoordinate(''),),
     'data_type': <IDSDataType.FLT: 'FLT'>,
     'documentation': 'Generic time',
     'maxoccur': None,
     'name': 'time',
     'ndim': 1,
     'path': IDSPath('time'),
     'path_doc': 'time(:)',
     'timebasepath': 'time',
     'type': 'dynamic',
     'units': 's'}


.. seealso::
    API documentation for :py:class:`~imaspy.ids_metadata.IDSMetadata`.
