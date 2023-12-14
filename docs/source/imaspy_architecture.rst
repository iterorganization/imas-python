IMASPy Architecture
===================

This document provides a brief overview of the architecture of IMASPy.

Data Dictionary metadata
------------------------

These classes are used to parse and represent IDS metadata from the Data Dictionary.
Metadata objects are generated from a Data Dictionary XML and are (supposed to be)
immutable.

-   :py:mod:`imaspy.ids_metadata` contains the main metadata class
    :py:class:`~imaspy.ids_metadata.IDSMetadata`. This class is generated from an
    ``<IDS>`` or ``<field>`` element in the Data Dictionary XML and contains all
    (parsed) data belonging to that ``<IDS>`` or ``<field>``. Most of the (Python)
    attributes correspond directly to an attribute of the XML element.

    This module also contains the :py:class:`~imaspy.ids_metadata.IDSType` enum. This
    enum corresponds to the Data Dictionary notion of ``type`` which can be ``dynamic``,
    ``constant``, ``static`` or unavailable on a Data Dictionary element.

-   :py:mod:`imaspy.ids_coordinates` contains two classes:
    :py:class:`~imaspy.ids_coordinates.IDSCoordinate`, which handles the parsing of
    coordinate identifiers from the Data Dictionary, and
    :py:class:`~imaspy.ids_coordinates.IDSCoordinates`, which handles coordinate
    retrieval and validation of IDS nodes.

    :py:class:`~imaspy.ids_coordinates.IDSCoordinate`\ s are created for each coordinate
    attribute of a Data Dictionary element: ``coordinate1``, ``coordinate2``, ...
    ``coordinate1_same_as``, etc.

    :py:class:`~imaspy.ids_coordinates.IDSCoordinates` is created and assigned as
    ``coordinates`` attribute of :py:class:`~imaspy.ids_struct_array.IDSStructArray` and
    :py:class:`~imaspy.ids_primitive.IDSPrimitive` objects. This class is responsible
    for retrieving coordinate values and for checking the coordinate consistency in
    :py:func:`~imaspy.ids_toplevel.IDSToplevel.validate`.

-   :py:mod:`imaspy.ids_data_type` handles parsing Data Dictionary ``data_type``
    attributes (see method :py:meth:`~imaspy.ids_data_type.IDSDataType.parse`) to an
    :py:class:`~imaspy.ids_data_type.IDSDataType` and number of dimensions.

    :py:class:`~imaspy.ids_data_type.IDSDataType` also has attributes for default values
    and mappings to Python / Numpy / Access Layer type identifiers.

-   :py:mod:`imaspy.ids_path` handles parsing of IDS paths to
    :py:class:`~imaspy.ids_path.IDSPath` objects. Paths can occur as the ``path``
    attribute of Data Dictionary elements, and inside coordinate identifiers.


Data Dictionary building and loading
------------------------------------

The following submodules are responsible for building the Data Dictionary and loading DD
definitions at runtime.

-   :py:mod:`imaspy.dd_helpers` handles building the ``IDSDef.zip`` file, containing all
    versions of the Data Dictionary since ``3.22.0``.

-   :py:mod:`imaspy.dd_zip` handles loading the Data Dictionary definitions at run time.
    These definitions can be loaded from an ``IDSDef.zip`` or from a custom XML file.


IDS nodes
---------

The following submodules and classes represent IDS nodes.

-   :py:mod:`imaspy.ids_base` defines the base class for all IDS nodes:
    :py:class:`~imaspy.ids_base.IDSBase`. This class is an abstract class and shouldn't
    be instatiated directly.

    Several useful properties are defined in this class, which are therefore available
    on any IDS node:

    -   ``_time_mode`` returns the ``ids_properties/homogeneous_time`` node
    -   ``_parent`` returns the parent object. Some examples:

        .. code-block:: python

            >>> core_profiles = imaspy.IDSFactory().core_profiles()
            >>> core_profiles._parent
            <imaspy.ids_factory.IDSFactory object at 0x7faa06bfac70>
            >>> core_profiles.ids_properties._parent
            <IDSToplevel (IDS:core_profiles)>
            >>> core_profiles.ids_properties.homogeneous_time._parent
            <IDSStructure (IDS:core_profiles, ids_properties)>
            >>> core_profiles.profiles_1d.resize(1)
            >>> core_profiles.profiles_1d[0]._parent
            <IDSStructArray (IDS:core_profiles, profiles_1d with 1 items)>
            >>> core_profiles.profiles_1d[0].time._parent
            <IDSStructure (IDS:core_profiles, profiles_1d[0])>

    -   ``_dd_parent`` returns the "data-dictionary" parent. This is usually the same as
        the ``_parent``, except for Arrays of Structures:

        .. code-block:: python

            >>> core_profiles = imaspy.IDSFactory().core_profiles()
            >>> core_profiles._dd_parent
            <imaspy.ids_factory.IDSFactory object at 0x7faa06bfac70>
            >>> core_profiles.ids_properties._dd_parent
            <IDSToplevel (IDS:core_profiles)>
            >>> core_profiles.ids_properties.homogeneous_time._dd_parent
            <IDSStructure (IDS:core_profiles, ids_properties)>
            >>> core_profiles.profiles_1d.resize(1)
            >>> # Note: _dd_parent for this structure is different from its parent:
            >>> core_profiles.profiles_1d[0]._dd_parent
            <IDSStructure (IDS:core_profiles, ids_properties)>
            >>> core_profiles.profiles_1d[0].time._parent
            <IDSStructure (IDS:core_profiles, profiles_1d[0])>

    -   ``_path`` gives the path to this IDS node, including Array of Structures
        indices.
    -   ``_lazy`` indicates if the IDS is lazy loaded.
    -   ``_version`` is the Data Dictionary version of this node.
    -   ``_toplevel`` is a shortcut to the :py:class:`~imaspy.ids_toplevel.IDSToplevel`
        element that this node is a decendent of.

-   :py:mod:`imaspy.ids_primitive` contains all data node classes, which are child
    classes of :py:class:`~imaspy.ids_primitive.IDSPrimitive`. ``IDSPrimitive``
    implements all functionality that is common for every data type, whereas the
    classes in below list are specific per data type.

    Assignment-time data type checking is handled by the setter of the
    :py:attr:`~imaspy.ids_primitive.IDSPrimitive.value` property and the ``_cast_value``
    methods on each of the type specialization classes.

    -   :py:class:`~imaspy.ids_primitive.IDSString0D` is the type specialization for 0D
        strings. It can be used as if it is a python :external:py:class:`str` object.
    -   :py:class:`~imaspy.ids_primitive.IDSString1D` is the type specialization for 1D
        strings. It behaves as if it is a python :external:py:class:`list` of
        :external:py:class:`str`.
    -   :py:class:`~imaspy.ids_primitive.IDSNumeric0D` is the base class for 0D
        numerical types:

        -   :py:class:`~imaspy.ids_primitive.IDSComplex0D` is the type specialization
            for 0D complex numbers. It can be used as if it is a python
            :external:py:class:`complex`.
        -   :py:class:`~imaspy.ids_primitive.IDSFloat0D` is the type specialization
            for 0D floating point numbers. It can be used as if it is a python
            :external:py:class:`float`.
        -   :py:class:`~imaspy.ids_primitive.IDSInt0D` is the type specialization
            for 0D whole numbers. It can be used as if it is a python
            :external:py:class:`int`.

    -   :py:class:`~imaspy.ids_primitive.IDSNumericArray` is the type specialization for
        any numeric type with at least one dimension. It can be used as if it is a
        :external:py:class:`numpy.ndarray`.

-   :py:mod:`imaspy.ids_struct_array` contains the
    :py:class:`~imaspy.ids_struct_array.IDSStructArray` class, which models Arrays of
    Structures. It also contains some :ref:`dev lazy loading` logic.

-   :py:mod:`imaspy.ids_structure` contains the
    :py:class:`~imaspy.ids_structure.IDSStructure` class, which models Structures. It
    contains the :ref:`lazy instantiation` logic and some of the :ref:`dev lazy loading`
    logic.

-   :py:mod:`imaspy.ids_toplevel` contains the
    :py:class:`~imaspy.ids_toplevel.IDSToplevel` class, which is a subclass of
    :py:class:`~imaspy.ids_structure.IDSStructure` and models toplevel IDSs.

    It implements some API methods that are only available on IDSs, such as
    ``validate``and ``(de)serialize``, and overwrites implementations of some
    properties.


.. _`lazy instantiation`:

Lazy instantiation
''''''''''''''''''

IDS nodes are instantiated only when needed. This is handled by
``IDSStructure.__getattr__``. When a new IDS Structure is created, it initially doesn't
have any IDS child nodes instantiated:

.. code-block:: python

    >>> import imaspy
    >>> # Create an empty IDS
    >>> cp = imaspy.IDSFactory().core_profiles()
    >>> # Show which elements are already created, hiding private attributes:
    >>> list(cp.__dict__)
    ['_lazy', '_children', '_parent', 'metadata', '__doc__', '_lazy_context']
    >>> # When we request a child element, it is automatically created:
    >>> cp.time
    <IDSNumericArray (IDS:core_profiles, time, empty FLT_1D)>
    >>> [child for child in cp.__dict__ if not child.startswith("_")]
    ['_lazy', '_children', '_parent', 'metadata', '__doc__', '_lazy_context',
     'time', '_toplevel']

This improves performance by creating less python objects: in most use cases, only a
subset of the nodes in an IDS will be used. These use cases benefit a lot from this lazy
instantiation.


.. _`dev lazy loading`:

Lazy loading
''''''''''''

:ref:`lazy loading` defers reading the data from the backend in a
:py:meth:`~imaspy.db_entry.DBEntry.get` or :py:meth:`~imaspy.db_entry.DBEntry.get_slice`
until the data is requested. This is handled in two places:

1.  ``IDSStructure.__getattr__`` implements the lazy loading alongside the lazy
    instantiation. When a new element is created by lazy instantiation, it will call
    ``imaspy.db_entry_helpers._get_child`` to lazy load this element:

    -   When the element is a data node (``IDSPrimitive`` subclass), the data for this
        element is loaded from the backend.
    -   When the element is another structure, nothing needs to be loaded from the
        backend. Only when a data node inside the structure is accessed, data needs to
        be loaded from the backend. Instead, we store the ``context`` on the created
        ``IDSStructure`` and loading is handled recursively.
    -   When the element is an Array of Structures, we also only store the ``context``
        on the created ``IDSStructArray``. Loading is handled as described in point 2.

2.  ``IDSStructArray._load`` implements the lazy loading of array of structures and
    their elements. This is triggered whenever an element is accessed (``__getitem__``)
    or the size of the Array of Structures is requested (``__len__``).


Creating and loading IDSs
-------------------------

-   :py:mod:`imaspy.db_entry`
-   :py:mod:`imaspy.db_entry_helpers`
-   :py:mod:`imaspy.ids_factory`


Access Layer interfaces
-----------------------

-   :py:mod:`imaspy.al_context`
-   :py:mod:`imaspy.ids_defs`
-   :py:mod:`imaspy.imas_interface`


MDSplus support
---------------

-   :py:mod:`imaspy.mdsplus_model`


Versioning
----------

Something about versioneer and :py:mod:`_version.py`


Miscelleneous
-------------

-   :py:mod:`imaspy.exception`
-   :py:mod:`imaspy.ids_convert`
-   :py:mod:`imaspy.setup_logging`
-   :py:mod:`imaspy.training`
-   :py:mod:`imaspy.util` and :py:mod:`imaspy._util`
