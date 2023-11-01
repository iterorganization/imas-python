import random
from unittest.mock import patch, DEFAULT

import pytest

from imaspy.db_entry import DBEntry
from imaspy.ids_defs import (
    IDS_TIME_MODE_HETEROGENEOUS,
    PREVIOUS_INTERP,
    ASCII_BACKEND,
    MEMORY_BACKEND,
)
from imaspy.ids_factory import IDSFactory
from imaspy.imas_interface import lowlevel, ll_interface
from imaspy.test.test_helpers import compare_children, fill_consistent, open_dbentry


def test_lazy_load_aos(backend, worker_id, tmp_path, log_lowlevel_calls):
    if backend == ASCII_BACKEND:
        pytest.skip("Lazy loading is not supported by the ASCII backend.")
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path, dd_version="3.39.0")
    ids = dbentry.factory.new("core_profiles")
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HETEROGENEOUS
    ids.profiles_1d.resize(10)
    for i in range(10):
        ids.profiles_1d[i].time = i
    dbentry.put(ids)

    # Test a random access pattern of the AOS elements
    lazy_ids = dbentry.get("core_profiles", lazy=True)
    random_list = list(range(10))
    random.shuffle(random_list)
    for i in random_list:
        assert lazy_ids.profiles_1d[i].time == i
    # Now all profiles_1d/time are loaded, check that we use loaded values and do not
    # read data from the lowlevel
    if ll_interface._al_version.major == 4:
        to_patch = {"ual_read_data": DEFAULT, "ual_begin_arraystruct_action": DEFAULT}
    else:
        to_patch = {"al_read_data": DEFAULT, "al_begin_arraystruct_action": DEFAULT}
    with patch.multiple(lowlevel, **to_patch) as values:
        assert len(lazy_ids.profiles_1d) == 10
        for i in range(10):
            assert lazy_ids.profiles_1d[i].time == i
        for method in to_patch:
            assert values[method].call_count == 0

    # Test get_slice
    lazy_ids_slice = dbentry.get_slice("core_profiles", 3.5, PREVIOUS_INTERP, lazy=True)
    assert lazy_ids_slice.profiles_1d.shape == (1,)
    assert lazy_ids_slice.profiles_1d[0].time == 3


def test_lazy_loading_distributions_random(backend, worker_id, tmp_path):
    if backend == ASCII_BACKEND:
        pytest.skip("Lazy loading is not supported by the ASCII backend.")
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path)
    ids = IDSFactory().new("distributions")
    fill_consistent(ids)
    dbentry.put(ids)

    lazy_ids = dbentry.get("distributions", lazy=True)
    compare_children(ids, lazy_ids)


def test_lazy_load_close_dbentry(requires_imas):
    dbentry = DBEntry(MEMORY_BACKEND, "ITER", 1, 1)
    dbentry.create()

    ids = dbentry.factory.core_profiles()
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HETEROGENEOUS
    dbentry.put(ids)

    lazy_ids = dbentry.get("core_profiles", lazy=True)
    dbentry.close()

    with pytest.raises(RuntimeError):
        print(lazy_ids.time)


def test_lazy_load_readonly(requires_imas):
    dbentry = DBEntry(MEMORY_BACKEND, "ITER", 1, 1)
    dbentry.create()

    ids = dbentry.factory.core_profiles()
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HETEROGENEOUS
    ids.time = [1, 2]
    dbentry.put(ids)

    lazy_ids = dbentry.get("core_profiles", lazy=True)

    # AoS modifiers
    with pytest.raises(ValueError):
        lazy_ids.profiles_1d.resize(1)
    with pytest.raises(ValueError):
        lazy_ids.profiles_1d.append(lazy_ids.profiles_1d._element_structure)
    with pytest.raises(ValueError):
        lazy_ids.profiles_1d[0] = None

    # Set IDSPrimitive
    with pytest.raises(ValueError):
        lazy_ids.ids_properties.homogeneous_time = 1
    with pytest.raises(ValueError):
        lazy_ids.time = [1, 2]
    # Modify numpy arrays
    with pytest.raises(ValueError):
        lazy_ids.time.resize(3)
    with pytest.raises(ValueError):
        lazy_ids.time.value[0] = 10


def test_lazy_load_no_put(requires_imas):
    dbentry = DBEntry(MEMORY_BACKEND, "ITER", 1, 1)
    dbentry.create()

    ids = dbentry.factory.core_profiles()
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HETEROGENEOUS
    dbentry.put(ids)

    lazy_ids = dbentry.get("core_profiles", lazy=True)

    with pytest.raises(ValueError):
        dbentry.put(lazy_ids)
    with pytest.raises(ValueError):
        dbentry.put_slice(lazy_ids)
