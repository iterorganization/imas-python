from packaging.version import Version
import pytest

import imaspy
from imaspy.imas_interface import ll_interface
from imaspy.test.test_helpers import open_dbentry


@pytest.fixture
def filled_dbentry(backend, worker_id, tmp_path):
    if backend == imaspy.ids_defs.MEMORY_BACKEND:
        pytest.skip("list_occurrences is not implemented for the MEMORY backend")
    entry = open_dbentry(backend, "w", worker_id, tmp_path)

    for i in range(3):
        cp = entry.factory.core_profiles()
        cp.ids_properties.homogeneous_time = 0
        cp.ids_properties.comment = f"core_profiles occurrence {i}"
        entry.put(cp, i)

    for i in [0, 1, 3, 6]:
        mag = entry.factory.magnetics()
        mag.ids_properties.homogeneous_time = 0
        mag.ids_properties.comment = f"magnetics occurrence {i}"
        entry.put(mag, i)

    yield entry
    entry.close()


def test_list_occurrences_no_path(filled_dbentry):
    if ll_interface._al_version >= Version("5.1"):
        occurrences = filled_dbentry.list_all_occurrences("core_profiles")
        assert occurrences == [0, 1, 2]

        occurrences = filled_dbentry.list_all_occurrences("magnetics")
        assert occurrences == [0, 1, 3, 6]

        assert filled_dbentry.list_all_occurrences("core_sources") == []

    else:  # AL 5.0 or lower
        with pytest.raises(RuntimeError):
            filled_dbentry.list_all_occurrences("core_profiles")
        with pytest.raises(RuntimeError):
            filled_dbentry.list_all_occurrences("magnetics")
        with pytest.raises(RuntimeError):
            filled_dbentry.list_all_occurrences("core_sources")


def test_list_occurrences_with_path(backend, filled_dbentry):
    if backend == imaspy.ids_defs.ASCII_BACKEND:
        pytest.skip("Lazy loading is not supported by the ASCII backend")

    comment = "ids_properties/comment"
    if ll_interface._al_version >= Version("5.1"):
        res = filled_dbentry.list_all_occurrences("core_profiles", comment)
        assert res[0] == [0, 1, 2]
        assert res[1] == [
            "core_profiles occurrence 0",
            "core_profiles occurrence 1",
            "core_profiles occurrence 2",
        ]

        res = filled_dbentry.list_all_occurrences("magnetics", comment)
        assert res[0] == [0, 1, 3, 6]
        assert res[1] == [
            "magnetics occurrence 0",
            "magnetics occurrence 1",
            "magnetics occurrence 3",
            "magnetics occurrence 6",
        ]

        res = filled_dbentry.list_all_occurrences("core_sources", comment)
        assert res == ([], [])

    else:  # AL 5.0 or lower
        with pytest.raises(RuntimeError):
            filled_dbentry.list_all_occurrences("core_profiles", comment)
        with pytest.raises(RuntimeError):
            filled_dbentry.list_all_occurrences("magnetics", comment)
        with pytest.raises(RuntimeError):
            filled_dbentry.list_all_occurrences("core_sources", comment)
