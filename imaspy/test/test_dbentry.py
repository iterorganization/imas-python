import pytest

import imaspy


def test_dbentry_contextmanager():
    entry = imaspy.DBEntry(imaspy.ids_defs.MEMORY_BACKEND, "test", 1, 1)
    entry.create()
    ids = entry.factory.core_profiles()
    ids.ids_properties.homogeneous_time = 0
    ids.ids_properties.comment = "test context manager"
    entry.put(ids)

    with imaspy.DBEntry(imaspy.ids_defs.MEMORY_BACKEND, "test", 1, 1) as entry2:
        ids2 = entry2.get("core_profiles")
        assert ids2.ids_properties.comment == ids.ids_properties.comment

    # Check that entry2 was closed
    assert entry2._db_ctx is None


@pytest.mark.skipif(
    imaspy.imas_interface.ll_interface._al_version.major < 5,
    reason="URI API not available for AL4",
)
def test_dbentry_contextmanager_uri(tmp_path):
    entry = imaspy.DBEntry(f"imas:ascii?path={tmp_path}/testdb", "w")
    ids = entry.factory.core_profiles()
    ids.ids_properties.homogeneous_time = 0
    ids.ids_properties.comment = "test context manager"
    entry.put(ids)

    with imaspy.DBEntry(f"imas:ascii?path={tmp_path}/testdb", "r") as entry2:
        ids2 = entry2.get("core_profiles")
        assert ids2.ids_properties.comment == ids.ids_properties.comment

    # Check that entry2 was closed
    assert entry2._db_ctx is None
