IMASPy 5 minute introduction
----------------------------

.. contents:: Contents
    :local:
    :depth: 1


Verify your IMAS installation
'''''''''''''''''''''''''''''

Before continuing, verify that your imaspy install is working. Check the
:ref:`Installing IMASPy` page for installation instructions if below fails for
you. Start python and import imaspy. Note that the version in below output may
be outdated.

.. code-block:: python

    >>> import imaspy
    >>> print(imaspy.__version__)
    0.6.2

.. note::

    If you have an IMASPy install without the IMAS Access Layer, importing
    IMASPy will display an error message. You can still use IMASPy, but not all
    functionality is available.


Create and use an IDS
'''''''''''''''''''''

To create an IDS, you must first make an :py:class:`~imaspy.ids_root.IDSRoot`
object. The IDS root is necessary for specifying which version of the IMAS Data
Dictionary you want to use (the last available one, by default). See
:ref:`Loading multiple DD versions in the same environment` for more information
on different Data Dictionary versions.

.. code-block:: python

    >>> import imaspy
    >>> import numpy as np
    >>> ids_root = imaspy.ids_root.IDSRoot()
    10:26:51 [INFO] Generating IDS structures for version 3.38.1 @ids_root.py:130
    >>> # Create an empty core_profiles IDS
    >>> core_profiles = ids_root.core_profiles
    >>> # Caution: doing this a second time does not create a new one:
    >>> core_profiles2 = ids_root.core_profiles
    >>> core_profiles is core_profiles2
    True

We can now use this ``core_profiles`` IDS and assign some data to it:

.. code-block:: python

    >>> core_profiles.ids_properties.comment = "Testing IMASPy"
    >>> core_profiles.ids_properties.homogeneous_time = imaspy.ids_defs.IDS_TIME_MODE_HOMOGENEOUS
    >>> # array quantities are automatically converted to the appropriate numpy arrays
    >>> core_profiles.time = [1, 2, 3]
    >>> # the python list of ints is converted to a 1D array of floats
    >>> core_profiles.time.value
    array([1., 2., 3.])
    >>> # resize the profiles_1d array of structures to match the size of `time`
    >>> core_profiles.profiles_1d.resize(3)
    >>> len(core_profiles.profiles_1d.value)
    3
    >>> # assign some data for the first time slice
    >>> core_profiles.profiles_1d[0].grid.rho_tor_norm = [0, 0.5, 1.0]
    >>> core_profiles.profiles_1d[0].j_tor = [0, 0, 0]

.. note::

    Until :issue:`IMAS-4680` is addressed, you should use :code:`.value` to get the
    value of a quantity in IMASPy.

As you can see in above example, IMASPy automatically checks the data you try to
assign to an IDS with the data type specified in the Data Dictionary. When
possible, your data is automatically converted to the expected type. You will
get an error message if this is not possible:

.. code-block:: python

    >>> core_profiles.time = "Cannot be converted"
    ValueError: could not convert string to float: 'Cannot be converted'
    >>> core_profiles.time = 1-1j
    TypeError: can't convert complex to float
    >>> core_profiles.ids_properties.source = 1-1j  # automatically converted to str
    >>> core_profiles.ids_properties.source.value
    '(1-1j)'


Store an IDS to disk
''''''''''''''''''''

.. note::

    - This functionality requires the IMAS Access Layer.
    - This API will change when IMASPy is moving to Access Layer 5 (expected Q2
      2023).

To store an IDS to disk, we need to indicate the following information to the
IMAS Access Layer. Please check the IMAS Access Layer documentation for more
information on this.

- ``shot``
- ``run``
- ``user``
- ``tokamak`` (also known as database)
- ``version`` (major version of the access layer, typically ``"3"``)
- Optional: which backend to use (e.g. the default MDSplus or HDF5).

In IMASPy you do this as follows:

.. code-block:: python

    >>> # you can specify shot=10 and run=2 when creating the IDSRoot object
    >>> #ids_root = imaspy.ids_root.IDSRoot(s=10, r=2)
    >>> # you can also set this after creating the ids_root object
    >>> # as long as you do it before create_env_backend
    >>> ids_root.shot = 10
    >>> ids_root.run = 2
    >>> # Create a new IMAS data entry for storing the core_profiles IDS we created earlier
    >>> # Here we specify user, tokamak, version and the backend
    >>> import os
    >>> ids_root.create_env_backend(user=os.environ['USER'], tokamak="ITER", version="3", backend_type=imaspy.ids_defs.HDF5_BACKEND)
    10:29:13 [INFO] Opening AL backend HDF5 for ITER (shot 10, run 2, user sebregm, ver 3, mode w) @ids_root.py:337
    (0, 1)
    >>> # now store the core_profiles IDS we just populated
    >>> ids_root.core_profiles.put()


Load an IDS from disk
'''''''''''''''''''''

.. note::

    - This functionality requires the IMAS Access Layer.
    - This API will change when IMASPy is moving to Access Layer 5 (expected Q2
      2023).

To load an IDS from disk, you need to specify the same information as
when storing the IDS (see previous section). Once a data entry is opened, you
can use ``<IDS>.get()`` to load IDS data from disk: 

.. code-block:: python

    >>> # Now load the core_profiles IDS back into a fresh ids_root object
    >>> ids_root2 = imaspy.ids_root.IDSRoot(s=10, r=2)
    10:29:56 [INFO] Generating IDS structures for version 3.38.1 @ids_root.py:130
    >>> ids_root2.open_env_backend(user=os.environ['USER'], tokamak="ITER", version="3", backend_type=imaspy.ids_defs.HDF5_BACKEND)
    10:30:07 [INFO] Opening AL backend HDF5 for ITER (shot 10, run 2, user sebregm, ver 3, mode r) @ids_root.py:337
    (0, 2)
    >>> ids_root2.core_profiles.get()
    >>> print(ids_root2.core_profiles.ids_properties.comment.value)
    Testing IMASPy
