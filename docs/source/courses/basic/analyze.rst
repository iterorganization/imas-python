Analyze with IMASPy
===================

.. TODO:: Add content

Loading IMAS data
-----------------

For this part of the training we will learn to open an IMAS database entry, and
plot some basic data in it using `matplotlib <https://matplotlib.org/>`.

Open an IMAS database entry
'''''''''''''''''''''''''''
IMAS explicitly separates the data on disk from the data in memory. To get
started we load an existing IMAS data file from disk. The on-disk file
is represented by an `imas.DBEntry`, which we have to
:meth:`~imaspy.ids_root.IDSRoot.open_env` to get a reference to the data file we
will manipulate. The connection to the data file is kept intact until we neatly
:meth:`~imaspy.ids_root.IDSRoot.close()` the file. Note that the on-disk file
will not be changed until an explicit ``.put()`` (e.g.
:meth:`~imaspy.ids_toplevel.IDSToplevel.put`) is called. This is similar to e.g.
a `xarray Dataset <https://docs.xarray.dev/en/stable/getting-started-guide/quick-overview.html#datasets>`_.
We load data in memory with the `get` and `get_slice` commands, after which we
can use it as normal Python data.

.. tabs::

    .. tab:: Exercise
        For the ``shot/run/user/database`` = ``134173/106/public/ITER`` scenario:

        * Read and print the ``time`` of the ``equilibrium`` IDS for the whole
          scenario
        * Read and print the electron temperature profile in the
          ``equilibrium`` IDS at time slice t=253s

    .. tab:: AL4
        .. literalinclude:: al4_snippets/read_whole_equilibrium.py

    .. tab:: IMASPy
        .. literalinclude:: imaspy_snippets/read_whole_equilibrium.py

When dealing with unknown data, it can be dangerous to blindly load whole IDSs.
For sure when dealing with larger data files, this might fill up the RAM of your
machine quickly. To deal with this we use partial_get, which allows us to load
only a small part of the IDS into memory. One first needs to know some names
and/or coordinates inside the data structure though!

.. tabs::
    .. tab:: Exercise
        Read the time array of the equilibrium IDS to get the time trace of a
        given scenario. This is how e.g, one can find the index corresponding a
        specific time slice.

    .. tab:: AL4
        .. literalinclude:: al4_snippets/read_equilibrium_time_array.py

    .. tab:: IMASPy
        .. literalinclude:: imaspy_snippets/read_equilibrium_time_array.py

Dealing with large IDSs
'''''''''''''''''''''''
If the data structure is too large and it order to save time and memory, one can
decide to read only the :math:`T_e` profile of the ``core_profiles`` IDS at
``t=253s``. As before, one has to know that it corresponds to ``index=261`` of
the core_profiles.time array, which can be found with the method above. This
assumes that the equilibrium and core_profiles IDSs are defined on the same time
array, which is not necessarily the case

.. tabs::
    .. tab:: Exercise
        Use ``partial_get`` to get the ``core_profiles`` :math:`T_e` and
        :math:`\rho_{tor_{norm}}` at ``index=261``
    .. tab:: AL4
        .. literalinclude:: al4_snippets/read_core_profiles_te_timeslice.py

    .. tab:: IMASPy
        .. literalinclude:: imaspy_snippets/read_core_profiles_te_timeslice.py


Now we can plot the :math:`T_e` profile obtained above:

.. tabs::
    .. tab:: Exercise
        Using ``matplotlib``, create a plot of :math:`T_e` on the y-axis and
        :math:`\rho_{tor_{norm}}` on the x-axis.
    .. tab:: AL4
        .. literalinclude:: al4_snippets/plot_core_profiles_te_timeslice.py

    .. tab:: IMASPy
        .. literalinclude:: imaspy_snippets/plot_core_profiles_te_timeslice.py
