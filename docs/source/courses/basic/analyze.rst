Analyze with IMASPy
===================

Loading IMAS data
-----------------

For this part of the training we will learn to open an IMAS database entry, and
plot some basic data in it using `matplotlib <https://matplotlib.org/>`_.

Open an IMAS database entry
'''''''''''''''''''''''''''
IMAS explicitly separates the data on disk from the data in memory. To get
started we load an existing IMAS data file from disk. The on-disk file
is represented by an ``imas.DBEntry``, which we have to
:meth:`~imaspy.ids_root.IDSRoot.open()` to get a reference to the data file we
will manipulate. The connection to the data file is kept intact until we neatly
:meth:`~imaspy.ids_root.IDSRoot.close()` the file. Note that the on-disk file
will not be changed until an explicit ``.put()`` (e.g.
:meth:`~imaspy.ids_toplevel.IDSToplevel.put()`) is called. This is similar to e.g.
a `xarray Dataset <https://docs.xarray.dev/en/stable/getting-started-guide/quick-overview.html#datasets>`_.
We load data in memory with the ``get`` and ``get_slice`` methods, after which we
can use it as normal Python data.

.. hint::
    Use the ASCII data supplied with IMASPy for all exercises. It contains two
    IDSs (``equilibrium`` and ``core_profiles``) filled  with data from three
    times slices of ITER reference data. To point to a local file we use the
    ``-prefix`` flag. Use the following boilerplate as start-off point for the
    exercises.

    .. code-block:: python

        import imaspy
        shot, run, user, database = 134173, 106, "public", "ITER"
        input = imaspy.DBEntry(imaspy.ids_defs.ASCII_BACKEND, database, shot, run)
        assets_path = files(imaspy) / "assets/"
        input.open(options=f"-prefix {assets_path}/")

.. tabs::

    .. tab:: Exercise
        For the example scenario ``shot = 134173``, ``run = 106``,
        ``user = "public"``, ``database = "ITER"``

        1. Read and print the ``time`` of the ``equilibrium`` IDS for the whole
           scenario
        2. Read and print the electron temperature profile (:math:`T_e`) in the
           ``equilibrium`` IDS at time slice t=433s

    .. tab:: AL4
        .. literalinclude:: al4_snippets/read_whole_equilibrium.py

    .. tab:: IMASPy
        .. literalinclude:: imaspy_snippets/read_whole_equilibrium.py

.. attention::
   When dealing with unknown data, it can be dangerous to blindly load data. For
   sure when dealing with larger data files, this might fill up the RAM of your
   machine quickly. The ASCII files supplied with IMASPy are small specifically
   for this purpose. IMASPy will allow to load a part of the data in the future
   using lazy-loading, see
   `IMAS-4506 <https://jira.iter.org/browse/IMAS-4506>`_.

.. tabs::
    .. tab:: Exercise
        Read the time array of the ``equilibrium`` IDS to get the time trace of
        a given scenario. This is how e.g, one can find the index corresponding
        a specific time slice.

    .. tab:: AL4
        .. literalinclude:: al4_snippets/read_equilibrium_time_array.py

    .. tab:: IMASPy
        .. literalinclude:: imaspy_snippets/read_equilibrium_time_array.py

.. attention::
    IMASPy objects generally behave the same way as numpy arrays. However, in
    some cases functions explicitly expect a pure numpy array. In this case, the
    ``.value`` attribute can be used to obtain the underlying data array.

    We are investigating options for improving the API (which may reduce, but
    not eliminate, the need for ``.value``). Progress for this can be followed
    on `IMAS-4680 <https://jira.iter.org/browse/IMAS-4680>`_.

.. attention::
    IMASPy has two main ways of accessing IDSs. In the exercises above, we used
    the "attribute-like" access. This is the main way of navigating the IDS tree.
    However, IMASPy also provides a "dict-like" interface to access data, which
    might be more convenient in some cases. For example:

    .. literalinclude:: imaspy_snippets/iterate_core_profiles.py


Using multiple IDSs
'''''''''''''''''''
If the data structure is too large and it order to save time and memory, one can
decide to only load the :math:`T_e` profile of the ``core_profiles`` IDS at
``t=433s``. As before, one has to know that it corresponds to ``index=1`` of
the ``core_profiles.time`` array, which can be found with the method above. This
assumes that the ``equilibrium`` and ``core_profiles`` IDSs are defined on the
same time array, which is not necessarily the case. Always check this when
working with random data!

.. tabs::
    .. tab:: Exercise
        Only assign the data you need to python variables and print
        ``core_profiles`` :math:`T_e` and :math:`\rho_{tor, norm}` at
        ``index=1``
    .. tab:: AL4
        .. literalinclude:: al4_snippets/read_core_profiles_te_timeslice.py

    .. tab:: IMASPy
        .. literalinclude:: imaspy_snippets/read_core_profiles_te_timeslice.py


Now we can plot the :math:`T_e` profile obtained above:

.. tabs::
    .. tab:: Exercise
        Using ``matplotlib``, create a plot of :math:`T_e` on the y-axis and
        :math:`\rho_{tor, norm}` on the x-axis.
    .. tab:: AL4
        .. literalinclude:: al4_snippets/plot_core_profiles_te_timeslice.py

    .. tab:: IMASPy
        .. literalinclude:: imaspy_snippets/plot_core_profiles_te_timeslice.py

.. figure:: core_profiles_te_timeslice.png
    :scale: 100%
    :alt: matplotlib plot of electron temperature vs normalized toroidal flux coordinate

    A plot of :math:`T_e` vs :math:`\rho_{tor, norm}`
