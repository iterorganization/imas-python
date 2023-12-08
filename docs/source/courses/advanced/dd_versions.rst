Working with multiple data dictionary versions
==============================================

Contrary to most high level interface for IMAS, IMASPy code is not tied to a specific
version of the Data Dictionary. In this lesson we will explore how IMASPy handles
different DD versions (including development builds of the DD), and how we can convert
IDSs between different versions of the Data Dictionary.

.. note::
    Most of the time you won't need to worry about DD versions and the default IMASPy
    behaviour should be fine.


The default Data Dictionary version
-----------------------------------

In the other training lessons, we didn't explicitly work with Data Dictionary versions.
Therefore IMASPy was always using the `default` DD version. Let's find out what that
version is:


Exercise 1: The default DD version
''''''''''''''''''''''''''''''''''

.. md-tab-set::

    .. md-tab-item:: Exercise

        1.  Create an :py:class:`imaspy.IDSFactory() <imaspy.ids_factory.IDSFactory>`.
        2.  Print the version of the DD that is used.
        3.  Create an empty IDS with this IDSFactory (any IDS is fine) and print the
            ``_version`` of the IDS. The ``_dd_version`` attribute of an IDS tells you
            the Data Dictionary version of this IDS. What do you notice?
        4.  Create an :py:class:`imaspy.DBEntry <imaspy.db_entry.DBEntry>`, you may use
            the :py:attr:`MEMORY_BACKEND <imaspy.ids_defs.MEMORY_BACKEND>`. Print the
            ``dd_version`` that is used. What do you notice?

    .. md-tab-item:: Solution

        .. literalinclude:: imaspy_snippets/dd_versions.py

Okay, so now you know what your default DD version is. But how is it determined? IMASPy
first checks if you have an IMAS environment loaded by checking the environment variable
``IMAS_VERSION``. If you are on a cluster and have used ``module load IMAS`` or similar,
this environment variable will indicate what data dictionary version this module is
using. IMASPy will use that version as its default.

If the ``IMAS_VERSION`` environment is not set, IMASPy will take the newest version of
the Data Dictionary that came bundled with it. Which brings us to the following topic:


Bundled Data Dictionary definitions
-----------------------------------

IMASPy comes bundled [#DDdefs]_ with many versions of the Data Dictionary definitions.
You can find out which versions are available by calling
:py:meth:`imaspy.dd_zip.dd_xml_versions`.


Converting an IDS between Data Dictionary versions
--------------------------------------------------

Newer versions of the Data Dictionary may introduce changes in IDS definitions. Some
things that could change:

-   Introduce a new IDS node
-   Remove an IDS node
-   Change the data type of an IDS node
-   Rename an IDS node

IMASPy can convert between different versions of the DD and will migrate the data as
much as possible. Let's see how this works in the following exercise.


Exercise 2: Convert an IDS between DD versions
''''''''''''''''''''''''''''''''''''''''''''''

.. md-tab-set::

    .. md-tab-item:: Exercise

        In this exercise we will work with a really old version of the data dictionary
        for the ``pulse_schedule`` IDS because a number of IDS nodes were renamed for
        this IDS.

        1.  Create an :py:class:`imaspy.IDSFactory() <imaspy.ids_factory.IDSFactory>`
            for DD version ``3.25.0``.
        2.  Create a ``pulse_schedule`` IDS with this IDSFactory and verify that it is
            using DD version ``3.25.0``.
        3.  Fill the IDS with some test data:

            .. literalinclude:: imaspy_snippets/ids_convert.py
                :start-after: # 3.
                :end-before: # 4.
        
        4.  Use :py:func:`imaspy.convert_ids <imaspy.ids_convert.convert_ids>` to
            convert the IDS to DD version 3.39.0. The ``antenna`` structure that we
            filled in the old version of the DD has since been renamed to ``launcher``,
            and the ``launching_angle_*`` structures to ``steering_angle``. Check that
            IMASPy has converted the data successfully (for example with
            :py:func:`imaspy.util.print_tree`).
        5.  By default, IMASPy creates a shallow copy of the data, which means that the
            underlying data arrays are shared between the IDSs of both versions. Update
            the ``time`` data of the original IDS (for example:
            :code:`pulse_schedule.time[1] = 3`) and print the ``time`` data of the
            converted IDS. Are they the same?

            .. note::

                :py:func:`imaspy.convert_ids <imaspy.ids_convert.convert_ids>` has an
                optional keyword argument ``deep_copy``. If you set this to ``True``,
                the converted IDS will not share data with the original IDS.

        6.  Update the ``ids_properties/comment`` in one version and print it in the
            other version. What do you notice?
        7.  Sometimes data cannot be converted, for example when a node was added or
            removed, or when data types have changed. For example, set
            ``pulse_schedule.ec.antenna[0].phase.reference_name = "Test refname"`` and
            perform the conversion to DD 3.39.0 again. What do you notice?

    .. md-tab-item:: Solution

        .. literalinclude:: imaspy_snippets/ids_convert.py


Automatic conversion between DD versions
----------------------------------------

.. TODO::
    TODO, first converge in this PR: https://git.iter.org/projects/IMAS/repos/imaspy/pull-requests/156/overview

    1.  Show and explain the default autoconvert behaviour
    2.  Use cases for disabling autoconvert
    3.  Show how disabled autoconvert works


Using custom builds of the Data Dictionary
------------------------------------------

In the previous sections we showed how you can direct IMASPy to use a specific released
version of the Data Dictionary definitions. Sometimes it is useful to work with
unreleased (development or custom) versions of the data dictionaries as well.

.. caution::

    Unreleased versions of the Data Dictionary should only be used for testing.
    
    Do not use an unreleased Data Dictionary version for long-term storage: data
    might not be read properly in the future.

If you build the Data Dictionary, a file called ``IDSDef.xml`` is created. This file
contains all IDS definitions. To work with a custom DD build, you need to point IMASPy
to this ``IDSDef.xml`` file:

.. code-block:: python
    :caption: Use a custom Data Dictionary build with IMASPy

    my_idsdef_file = "path/to/IDSDef.xml"  # Replace with the actual path

    # Point IDSFactory to this path:
    my_factory = imaspy.IDSFactory(xml_path=my_idsdef_file)
    # Now you can create IDSs using your custom DD build:
    my_ids = my_factory.new("...")

    # If you need a DBEntry to put / get IDSs in the custom version:
    my_entry = imaspy.DBEntry("imas:hdf5?path=my-testdb", "w", xml_path=my_idsdef_file)


Once you have created the ``IDSFactory`` and/or ``DBEntry`` pointing to your custom DD
build, you can use them like you normally would.


.. rubric:: Footnotes

.. [#DDdefs] To be more precise, the Data Dictionary definitions are generated when the
    IMASPy package is created. See :ref:`this reference <DD background>` for more
    details.
