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

-   :py:mod:`imaspy.dd_helpers`
-   :py:mod:`imaspy.dd_zip`


IDS nodes
---------

The following submodules and classes represent IDS nodes.

-   :py:mod:`imaspy.ids_base`
-   :py:mod:`imaspy.ids_primitive`
-   :py:mod:`imaspy.ids_struct_array`
-   :py:mod:`imaspy.ids_structure`
-   :py:mod:`imaspy.ids_toplevel`


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
