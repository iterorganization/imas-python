.. _`Using multiple DD versions in the same environment`:

Using multiple DD versions in the same environment
==================================================

Whereas the default IMAS High Level Interface is built for a single Data Dictionary
version, IMASPy can transparently handle multiple DD versions.

By default, IMASPy uses the same Data Dictionary version as the loaded IMAS environment
is using, as specified by the environment variable ``IMAS_VERSION``. If no IMAS
environment is loaded, the last available DD version is used.

You can also explicitly specify which IMAS version you want to use when constructing a
:py:class:`~imaspy.db_entry.DBEntry` or :py:class:`~imaspy.ids_factory.IDSFactory`. For
example:

.. code-block:: python
    :caption: Using non-default IMAS versions.

    import imaspy

    factory_default = imaspy.IDSFactory()  # Use default DD version
    factory_3_32_0 = imaspy.IDSFactory("3.32.0")  # Use DD version 3.32.0

    # Will write IDSs to the backend in DD version 3.32.0
    dbentry = imaspy.DBEntry(imaspy.ids_defs.HDF5_BACKEND, "TEST", 10, 2, version="3.32.0")
    dbentry.create()

.. seealso:: :ref:`multi-dd training`


Conversion of IDSs between DD versions
--------------------------------------

IMASPy can convert IDSs between different versions of the data dictionary. This uses the
"non-backwards compatible changes" metadata from the DD definitions. You can explicitly
convert IDSs using :py:func:`imaspy.convert_ids <imaspy.ids_convert.convert_ids>`:

.. code-block:: python
    :caption: Convert an IDS to a different DD version

    import imaspy

    # Create a pulse_schedule IDS in version 3.23.0
    ps = imaspy.IDSFactory("3.25.0").new("pulse_schedule")
    ps.ec.antenna.resize(1)
    ps.ec.antenna[0].name = "IDS conversion test"

    # Convert the IDS to version 3.30.0
    ps330 = imaspy.convert_ids(ps, "3.30.0")
    # ec.antenna was renamed to ec.launcher between 3.23.0 and 3.30.0
    print(len(ps330.ec.launcher))  # 1
    print(ps330.ec.launcher[0].name.value)  # IDS conversion test

.. note::

    Not all data may be converted. For example, when an IDS node is removed between DD
    versions, the corresponding data is not copied. IMASPy provides logging to indicate
    when this happens.

The DBEntry class automatically converts IDSs to the requested version:

- When doing a ``put`` or ``put_slice``, the provided IDS is first converted to the
  target version of the DBEntry and then put to disk.
- When doing a ``get`` or ``get_slice``, the IDS is first read from disk in the version
  as it was stored (by checking ``ids_properties/version_put/data_dictionary``) and then
  converted to the requested target version.


.. _`DD background`:

Background information
----------------------

Since IMASPy needs to have access to multiple DD versions it was chosen to
bundle these with the code at build-time, in setup.py. If a git clone of the
Data Dictionary succeeds, the setup tools automatically download saxon and
generate ``IDSDef.xml`` for each of the tagged versions in the DD git
repository. These are then gathered into ``IDSDef.zip``, which is
distributed inside the IMASPy package.

To update the set of data dictionaries new versions can be added to the zipfile.
A reinstall of the package will ensure that all available versions are included
in IMASPy. Additionally an explicit path to an XML file can be specified, which
is useful for development.

Automated tests have been provided that check the loading of all of the DD
versions tagged in the data-dictionary git repository.


Extending the DD set
''''''''''''''''''''

A new command has been defined python setup.py build_DD which fetches new tags
from git and builds IDSDef.zip

The IDSDef.zip search paths have been expanded:

- ``$IMASPY_DDZIP`` (path to a zip file)
- ``./IDSDef.zip``
- ``~/.config/imaspy/IDSDef.zip`` (``$XDG_CONFIG_DIR``)
- ``__file__/../assets/IDSDef.zip`` (provided with IMASPy)

All paths are searched in order.
