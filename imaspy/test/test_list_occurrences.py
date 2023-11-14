from packaging.version import Version
import pytest

import imaspy
from imaspy.imas_interface import ll_interface


@pytest.fixture
def filled_dbentry():
    entry = imaspy.DBEntry(imaspy.ids_defs.MEMORY_BACKEND, "test", 1, 1)
    entry.create()

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
    occurrences = filled_dbentry.list_all_occurrences("core_profiles")
    assert occurrences == [0, 1, 2]

    occurrences = filled_dbentry.list_all_occurrences("magnetics")
    if ll_interface._al_version >= Version("5.1"):
        assert occurrences == [0, 1, 3, 6]
    else:  # Our algorithm will stop after discovering occurrence 2 doesn't exist
        assert occurrences == [0, 1]

    assert filled_dbentry.list_all_occurrences("core_sources") == []


def test_list_occurrences_with_path(filled_dbentry):
    res = filled_dbentry.list_all_occurrences("core_profiles", "ids_properties/comment")
    assert res[0] == [0, 1, 2]
    assert res[1] == [
        "core_profiles occurrence 0",
        "core_profiles occurrence 1",
        "core_profiles occurrence 2",
    ]

    res = filled_dbentry.list_all_occurrences("magnetics", "ids_properties/comment")
    if ll_interface._al_version >= Version("5.1"):
        assert res[0] == [0, 1, 3, 6]
        assert res[1] == [
            "magnetics occurrence 0",
            "magnetics occurrence 1",
            "magnetics occurrence 3",
            "magnetics occurrence 6",
        ]
    else:  # Our algorithm will stop after discovering occurrence 2 doesn't exist
        assert res[0] == [0, 1]
        assert res[1] == ["magnetics occurrence 0", "magnetics occurrence 1"]
        
    res = filled_dbentry.list_all_occurrences("core_sources", "ids_properties/comment")
    assert res == ([], [])
