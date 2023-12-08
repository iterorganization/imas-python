Advanced data exploration
=========================

In the :ref:`basic/explore` training we have seen how to explore IMASPy data structures
in an interactive way.

In this lesson, we will go a step further and look at methods to explore IMASPy data
structures programmatically. This can be useful for, for example, writing plotting
tools, analysis scripts, etc.


Exploring IDS (sub)structures
-----------------------------

An IDS structure is a collection of IDS nodes (which could be structures, or arrays of
structures themselves). In IMASPy this is represented by the
:py:class:`~imaspy.ids_structure.IDSStructure` class. You will find these classes in a
lot of places:

- Data Dictionary IDSs is a special case of an IDS structure (implemented by class
  :py:class:`~imaspy.ids_toplevel.IDSToplevel`, which is a subclass of
  ``IDSStructure``).
- Data Dictionary structures, for example, the ``ids_properties`` structure that is
  present in every IDS.
- Data Dictionary arrays of structures (implemented by
  :py:class:`~imaspy.ids_struct_array.IDSStructArray`) contain ``IDSStructure``\ s.

When you have an ``IDSStructure`` object, you can iterate over it to get all child nodes
that are contained in this structure. See the following example:

.. code-block:: python

    import imaspy

    core_profiles = imaspy.IDSFactory().core_profiles()
    # core_profiles is an IDS toplevel, which is also a structure:
    
    print("Core profiles contains the following elements:")
    for child_node in core_profiles:
        print("-", child_node.metadata.name)
    print()

    print("Core profiles contains the following non-empty elements:")
    # If you only want to loop over child nodes that have some data in them:
    for filled_child_node in core_profiles._iter_nonempty():
        print("-", child_node.metadata.name)

.. note::

    :py:func:`IDSStructure._iter_nonempty
    <imaspy.ids_structure.IDSStructure._iter_nonempty>` may look like a private
    function, but it is part of the public API.

    The function name starts with an underscore so it does not interfere with potential
    names of children of the structure.


Exercise 1: Explore structures
''''''''''''''''''''''''''''''

.. md-tab-set::

    .. md-tab-item:: Exercise

        1.  Load the training data for the ``equilibrium`` IDS. You can refresh how to
            do this in the following section of the basic training material: :ref:`Open
            an IMAS database entry`.
        2.  Loop over all non-empty child nodes of this IDS and print their name.
        3.  Print all child nodes of the ``ids_properties`` structure and their value.
        
    .. md-tab-item:: Solution

        .. literalinclude:: imaspy_snippets/explore_structures.py


Explore IDS data nodes and arrays of structures
-----------------------------------------------

.. TODO::
    ...
