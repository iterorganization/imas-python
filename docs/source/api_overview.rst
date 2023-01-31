IMASPy in the IMAS ecosystem
============================

.. image:: imaspy_ecosystem.png

IMASPy builds on the IMAS-LowLevel Python native interface. At IMASPy build time,
a collection of data dictionaries is bundled into a file IDSDef.zip. At IMASPy
read time, all files in the proper paths named IDSDef.zip are searched for data
dictionary versions to support. Alternatively explicit paths to xml files can be
used.


IMASPy nested structure design
==============================

.. image:: imaspy_structure.png

IMASPy uses a tree-style layout, with four container types:

- :py:class:`IDSStructure` (extended :py:class:`IDSToplevel`)
- :py:class:`IDSStructArray`
- :py:class:`IDSNumericArray`
- :py:class:`IDSPrimitive`

And a root container, :py:class:`IDSRoot`, which contains several
:py:class:`IDSToplevels`.  Only :py:class:`IDSPrimitive` and
:py:class:`IDSNumericArray` contain actual
values. They are leaf nodes and can be iterated over separately.
:py:class:`IDSNumericArray` is a special case of :py:class:`IDSPrimitive,`
containing a collection of values instead of a single 0D value. The class
subclasses both :py:class:`IDSPrimitive` and NDArrayOperatorsMixin, allowing to
create numpy array-like classes. See
https://numpy.org/doc/stable/reference/generated/numpy.lib.mixins.NDArrayOperatorsMixin.html


IMASPy usage
============

The IMASPy project defines a class :py:class:`IDSRoot` which can be instantiated
with a DD version number or xml_path. It reads the XML file and recreates the
:py:class:`IDSes` in memory, as :py:class:`IDSToplevel` classes containing
:py:class:`IDSStructures,` :py:class:`IDSStructArrays,`
:py:class:`IDSPrimitives` and :py:class:`IDSNumericArrays.`

.. code-block:: python

    class IDSRoot:
        """ Root of IDS tree. Contains all top-level IDSs """
        def __init__(self, s=-1, r=-1, rs=None, rr=None, version=None,
            xml_path=None, backend_version=None, backend_xml_path=None,
            backend_version=None, backend_xml_path=None, _lazy=True):

The arguments to this function are:

1. Shot number s
2. Run number r
3. Reference Shot / Run not implemented (rs, rr)
4. Version = DD version (“3.30.0”), autoloads, defaults to latest_version if None
5. xml_path = explicit path to XML file (useful for development and testing)
6. backend_version = Version to assume for data store (autoloaded if None)
7. backend_xml_path = XML file to load for data store
8. _lazy = If True, only load the template of an :py:class:`IDSToplevel`  in
     memory if it is needed, e.g. if a node of the IDS is addressed. If
     False, load all IDSs on initialization time.

An example of instantiating this structure and opening an AL backend is:

.. code-block:: python

    ids = imaspy.ids_root.IDSRoot(1, 0, xml_path=xml_path)
    ids.open_ual_store(os.environ.get("USER", "root"), "test", "3", MDSPLUS_BACKEND, mode=mode)


`MDSPLUS_BACKEND` is the identifier from the Access Layer to select the MDSplus backend.


Loading multiple DD versions in the same environment
====================================================

The main change necessary to enable loading multiple DD versions into different
:py:class:`IDSRoots` is to enable the finding of the relevant
:py:class:`IDSDef.xml` files. In the ‘classical’ IMAS approach a single
:py:class:`IDSDef.xml` file is located in a directory specified by an
environment variable.

Since IMASPy needs to have access to multiple DD versions it was chosen to
bundle these with the code at build-time, in setup.py. If a git clone of the
data-dictionary/ succeeds the setup tools automatically download saxon and
generate :py:class:`IDSDef.xml` for each of the tagged versions in the DD git
repository. These are then gathered into :py:class:`IDSDef.zip,` which is
distributed inside the IMASPy package.

To update the set of data dictionaries new versions can be added to the zipfile.
A reinstall of the package will ensure that all available versions are included
in IMASPy. Additionally an explicit path to an XML file can be specified, which
is useful for development.

Automated tests have been provided that check the loading of all of the DD
versions tagged in the data-dictionary git repository.


Extending the DD set
--------------------

A new command has been defined python setup.py build_DD which fetches new tags
from git and builds IDSDef.zip

The IDSDef.zip search paths have been expanded:

- `$IMASPY_DDZIP` (path to a zip file)
- `./IDSDef.zip`
- `~/.config/imaspy/IDSDef.zip` ($XDG_CONFIG_DIR)
- `__file__/../assets/IDSDef.zip` (provided with IMASPy)

All paths are searched in order.


Conversion of IDSes between DD versions
=======================================

The conversion between DD versions hinges on the ability to read and write to a
backend data store in a different version than the current DD. To enable this, IMASPy
needs to read both the ‘main’ in-memory DD, as well as the ‘backend’ DD. This is
implemented by creating a new routine read_backend_xml on
:py:class:`IDSToplevel` and set_backend_properties on :py:class:`IDSStructure.`

.. code-block:: python

    class IDSToplevel(IDSStructure):
       def __init__(
            self, parent, name, structure_xml, backend_version=None, backend_xml_path=None
        ):
            super().__init__(parent, name, structure_xml)

            # Set an explicit backend_version or xml path
            # these will be used when put() or get() is called.
            self._backend_version = backend_version
            self._backend_xml_path = backend_xml_path

            if backend_xml_path or backend_version:
                self._read_backend_xml(backend_version, backend_xml_path)

        def _read_backend_xml(self, version=None, xml_path=None):
            """Find a DD xml from version or path, select the child corresponding to the
            current name and set the backend properties.

            This is defined on the Toplevel and not on the Root because that allows
            IDSes to be read from different versions. Still use the ElementTree memoization
            so performance will not suffer too much from this.
            """


`_read_backend_xml` finds the right DD xml to use, reads it, and
calls `set_backend_properties` with the subset corresponding to the
current IDS.

.. code-block:: python

   def set_backend_properties(self, structure_xml):
        """Walk the union of existing children and those in structure_xml
        and set backend_type annotations for this element and its children."""


This sets `_backend_type`, `_backend_name` and `_backend_ndims` on each
of the :py:class:`IDSPrimitives` encountered in a Depth-First Search.
The backend reading routines `get()` and `put()` then use these types
and dimensions when reading, if they are set.  Reading of data at an
unknown DD version before the :py:class:`IDSRoot` is created and the
backend is opened, the DD version of the IDS is unknown. At the time of
`get()` the DD version is found by `read_data_dictionary_version`, which
reads :py:class:`IDS_properties/version_put/data_dictionary`


Implicit conversions:
---------------------

- Add field
  - No data can be converted
- Delete field
  - No data can be converted
- Change data_type
  - Convert data on read/write
- Move field
  - Handled by searching for change_nbc_previous_name on backend and current XML
  - This is complex, since we may have to search many elements to find the one
    which was renamed. Changing depths makes this harder.
  - Currently implemented up to a single depth change, though multiple are
    possible within this design


There are some limitations of the change_nbc paradigm:
------------------------------------------------------

- Forward only
- May require reading an arbitrary number of intermediate versions
- Does not cover more complex migrations

IMASPy will not load intermediate versions. Double renames are therefore not
supported yet. This does not appear to be a problem so far. If any problem
occurs the conversion can easily be done in multiple steps.



Time slicing
============

The lowlevel API provides `ual_write_slice_data` to write only a slice (in the
last dimension, time) to the backend, as well as `ual_begin_slice_action`. After
that normal `get()` can be used. We have implemented time slicing support, with
two main entry points on :py:class:`IDSToplevel`:


.. code-block:: python

    def getSlice(
        self, time_requested, interpolation_method=CLOSEST_INTERP, occurrence=0
    ):
        """Get a slice from the backend.

        @param[in] time_requested time of the slice
        - UNDEFINED_TIME if not relevant (e.g to append a slice or replace the last slice)
        @param[in] interpolation_method mode for interpolation:
        - CLOSEST_INTERP take the slice at the closest time
        - PREVIOUS_INTERP take the slice at the previous time
        - LINEAR_INTERP interpolate the slice between the values of the previous and next slice
        - UNDEFINED_INTERP if not relevant (for write operations)
        """


    def putSlice(self, occurrence=0, ctx=None):
        """Put a single slice into the backend. only append is supported"""


These setup the backend in the right state and recursively call `get()`
and `put()` to perform their duties.

Test cases have been built to verify the required behaviour, in
`imaspy/test_time_slicing.py`, on the equilibrium IDS. There is no reason to
expect different behaviour for other IDSes.

Writing slice data (single slice and multiple slices at the same time) and
verifying as a global array Reading slice by slice (single slice only) The tests
pass on the memory and MDSPlus backend (the ASCII backend does not support
slicing).


Resampling
==========

For resampling of data we stick close to the numpy and scipy APIs. The relevant
method signatures are reproduced here:

.. code-block:: python

    Class scipy.interpolate.interp1d(x, y, kind='linear', axis=- 1, copy=True,
        bounds_error=None, fill_value=nan, assume_sorted=False)

Which produces a resampling function, whose call method uses interpolation to
find the value of new points. This can be used like so:

.. code-block:: python

    ids = IDSRoot()
    f = scipy.interpolate.interp1d(ids.pulse_schedule.time, ids.pulse_schedule_some_1d_var)
    ids.pulse_schedule.some_1d_var = f(ids.pulse_schedule.some_1d_var)


A more general approach would work on the basis of scanning the tree for
shared coordinates, and resampling those in the same manner (by creating a
local interpolator and applying it). The

.. code-block:: python

    visit_children(self, fun, leaf_only):

method defined on :py:class:`IDS_structure` and :py:class:`IDS_toplevel` can
be used for this. For a proof-of-concept it is recommended to only resample
in the time direction.

For example, a proposal implementation included in 0.4.0 can be used as such
(inplace interpolation on an IDS leaf node)

.. code-block:: python

    ids = imaspy.ids_root.IDSRoot(1, 0)
    ids.nbi.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.nbi.time = [1, 2, 3]
    ids.nbi.unit.resize(1)
    ids.nbi.unit[0].energy.data = 2 * ids.nbi.time
    old_id = id(ids.nbi.unit[0].energy.data)

    assert ids.nbi.unit[0].energy.data.time_axis == 0

    ids.nbi.unit[0].energy.data.resample(
        ids.nbi.time,
        [0.5, 1.5],
        ids.nbi.ids_properties.homogeneous_time,
        inplace=True,
        fill_value="extrapolate",
    )

    assert old_id == id(ids.nbi.unit[0].energy.data)
    assert ids.nbi.unit[0].energy.data == [1, 3]


Or as such (explicit in-memory copy + interpolation, producing a new data leaf/container):

.. code-block:: python

    ids = imaspy.ids_root.IDSRoot(1, 0)
    ids.nbi.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.nbi.time = [1, 2, 3]
    ids.nbi.unit.resize(1)
    ids.nbi.unit[0].energy.data = 2 * ids.nbi.time
    old_id = id(ids.nbi.unit[0].energy.data)

    assert ids.nbi.unit[0].energy.data.time_axis == 0

    new_data = ids.nbi.unit[0].energy.data.resample(
        ids.nbi.time,
        [0.5, 1.5],
        ids.nbi.ids_properties.homogeneous_time,
        inplace=False,
        fill_value="extrapolate",
    )

    assert old_id != id(new_data)
    assert new_data == [1, 3]


Implementation unit tests can be found in `test_latest_dd_resample.py`.


Alternative resampling methods
------------------------------

.. code-block:: python

    scipy.signal.resample(x, num, t=None, axis=0, window=None, domain='time')

`Scipy.signal.resample` uses a Fourier method to resample, which assumes the
signal is periodic. It can be very slow if the number of input or output
samples is large and prime. See
https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample.html
for more information.

.. code-block:: python

    scipy.signal.resample_poly(x, up, down, axis=0, window='kaiser', 5.0, padtype='constant', cval=None)

Could be considered, which uses a low-pass FIR filter. This assumes zero
values outside the boundary. See
https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html#scipy.signal.resample_poly
for more information.  We do not recommend to use simpler sampling methods
such as nearest-neighbour if possible, as this reduces the data quality and
does not result in a much simpler or faster implementation if care is taken.
