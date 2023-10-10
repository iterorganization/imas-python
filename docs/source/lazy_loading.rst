Lazy loading
============

When reading data from a data entry (using :meth:`DBEntry.get`, or
:meth:`DBEntry.get_slice`), by default all data is read immediately from the
lowlevel Access Layer backend. This may take a long time to complete if the data entry
has a lot of data stored for the requested IDS.

Instead of reading data immediately, IMASPy can also `lazy load` the data when you need
it. This will speed up your program in cases where you are interested in a subset of all
the data stored in an IDS.


Enable lazy loading of data
---------------------------

You can enable lazy loading of data by supplying the keyword argument :code:`lazy=True`
to :meth:`DBEntry.get`, or :meth:`DBEntry.get_slice`. The returned IDS
object will fetch the data from the backend at the moment that you want to access it.
See below example:

.. code-block:: python
    :caption: Example with lazy loading of data

    import imaspy
    from imaspy.ids_defs import MDSPLUS_BACKEND
    import numpy
    from matplotlib import pyplot as plt

    database, shot, run, user = "ITER", 134173, 106, "public"
    data_entry = imaspy.DBEntry(MDSPLUS_BACKEND, database, shot, run, user)
    data_entry.open()
    # Enable lazy loading with `lazy=True`:
    core_profiles = data_entry.get("core_profiles", lazy=True)

    # No data has been read from the lowlevel backend yet
    # The time array is loaded only when we access it on the following line:
    time = core_profiles.time.value
    print(f"Time has {len(time)} elements, between {time[0]} and {time[-1]}")

    # Find the electron temperature at rho=0 for all time slices
    electon_temperature_0 = numpy.array([
        p1d.electrons.temperature.value[0]
        for p1d in core_profiles.profiles_1d
    ])
    plt.plot(time, electon_temperature_0)
    plt.show()

In this example, using lazy loading is about 6 times faster than a regular
:code:`get()`.


Caveats of lazy loaded IDSs
---------------------------

Lazy loading of data may speed up your programs, but also comes with some limitations.

1.  IMASPy **assumes** that the underlying data entry is not modified.

    When you (or another user) overwrite or add data to the same data entry, you may end
    up with a mix of old and new data in the lazy loaded IDS.

2.  After you close the data entry, no new elements can be loaded.

    >>> core_profiles = data_entry.get("core_profiles", lazy=True)
    >>> data_entry.close()
    >>> print(core_profiles.time)
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
    RuntimeError: Cannot lazy load the requested data: the data entry is no longer
    available for reading. Hint: did you close() the DBEntry?

3.  IDSs that are lazy loaded are read-only, and you cannot :code:`put()` or
    :code:`put_slice()` them.
4.  Lazy loading has more overhead for reading data from the lowlevel: it is therefore
    more efficient to do a full :code:`get()` or :code:`get_slice()` when you intend to
    use most of the data stored in an IDS.
5.  When using IMASPy with remote data access (i.e. the UDA backend), a full
    :code:`get()` or :code:`get_slice()` is more efficient than lazy loading.
