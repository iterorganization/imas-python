.. _wrangler:

Wrangler — flat dict ↔ IDS
===========================

The :mod:`imas.wrangler` module converts between IMAS IDS objects and a
**flat Python dict** whose keys are dot-separated paths.

This is useful for machine-learning pipelines, inspection tools, and any
workflow that wants to treat IDS data as a plain mapping of named arrays.

Key functions
-------------

.. autofunction:: imas.wrangler.wrangle
.. autofunction:: imas.wrangler.unwrangle
.. autofunction:: imas.wrangler.ids_to_flat
.. autofunction:: imas.wrangler.split_location_across_ids


Flat-dict key format
--------------------

Every key is ``"<ids_name>.<field.path>"`` where the field path mirrors the
IDS structure hierarchy:

.. code-block:: text

    "core_profiles.time"
    "core_profiles.ids_properties.homogeneous_time"
    "core_profiles.profiles_1d.grid.rho_tor_norm"   # AoS path


Quick example
-------------

.. code-block:: python

    import numpy as np
    from imas.wrangler import wrangle, unwrangle

    # --- flat dict → IDS ------------------------------------------------
    flat = {
        "core_profiles.ids_properties.homogeneous_time": 1,
        "core_profiles.time": np.array([0.0, 1.0, 2.0]),
        # AoS: leading dimension = number of time slices
        "core_profiles.profiles_1d.grid.rho_tor_norm": np.tile(
            np.linspace(0, 1, 50), (3, 1)
        ),
        "core_profiles.profiles_1d.electrons.temperature": np.ones((3, 50)) * 1e3,
    }

    ids_dict = wrangle(flat)
    cp = ids_dict["core_profiles"]

    print(cp.time.value)             # array([0., 1., 2.])
    print(cp.profiles_1d.size)       # 3
    print(cp.profiles_1d[0].grid.rho_tor_norm.value.shape)  # (50,)

    # --- IDS → flat dict ------------------------------------------------
    recovered = unwrangle(list(flat.keys()), ids_dict)

    print(recovered["core_profiles.time"])          # array([0., 1., 2.])
    print(recovered["core_profiles.profiles_1d.electrons.temperature"].shape)  # (3, 50)

If you already have an IDS from a :py:class:`~imas.db_entry.DBEntry`, use
:func:`~imas.wrangler.ids_to_flat` — no path list required:

.. code-block:: python

    import imas
    from imas.wrangler import ids_to_flat

    with imas.DBEntry("imas:hdf5?path=./test", "r") as db:
        cp = db.get("core_profiles", autoconvert=False)

    flat = ids_to_flat(cp)
    print(flat["core_profiles.time"])
    print(flat["core_profiles.profiles_1d.electrons.temperature"].shape)


Array of Structures (AoS)
-------------------------

For paths that pass through an AoS node (e.g. ``profiles_1d``):

* **wrangle** — the value must have a leading dimension equal to the number of
  AoS elements.  The AoS is resized automatically on the first path that
  touches it; subsequent paths must agree on the same size.

* **unwrangle** — homogeneous AoS (all elements have the same leaf shape) is
  returned as a :class:`numpy.ndarray` with the AoS index as the leading axis.
  Ragged AoS (elements differ in length) requires
  `awkward-array <https://awkward-array.org>`__ and is returned as an
  :class:`awkward.Array`:

  .. code-block:: bash

      pip install "imas-python[awkward]"

  .. code-block:: python

      import awkward as ak
      from imas.wrangler import unwrangle

      result = unwrangle(["thomson_scattering.channel.t_e.data"], ids_dict)
      arr = result["thomson_scattering.channel.t_e.data"]
      # arr is an ak.Array when channels have different numbers of time points
