import pytest

import imaspy
from imaspy.exception import UnknownDDVersion
from imaspy.imas_interface import has_imas, ll_interface
from imaspy.test.test_helpers import compare_children


def test_dbentry_contextmanager(requires_imas):
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
    not has_imas or ll_interface._al_version.major < 5,
    reason="URI API not available",
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


def test_ignore_unknown_dd_version(monkeypatch):
    entry = imaspy.DBEntry("imas:memory?path=/", "w")
    ids = entry.factory.core_profiles()
    ids.ids_properties.homogeneous_time = 0
    ids.ids_properties.comment = "Test unknown DD version"
    # Put this IDS with an invalid DD version
    with monkeypatch.context() as m:
        m.setattr(entry.factory, "_version", "invalid DD version")
        assert entry.dd_version == "invalid DD version"
        entry.put(ids)

    with pytest.raises(UnknownDDVersion):
        entry.get("core_profiles")
    ids2 = entry.get("core_profiles", ignore_unknown_dd_version=True)
    assert ids2.ids_properties.version_put.data_dictionary == "invalid DD version"
    compare_children(ids, ids2)
    # Test that autoconvert plays nicely with this option as well
    ids3 = entry.get("core_profiles", ignore_unknown_dd_version=True, autoconvert=False)
    compare_children(ids, ids3)
