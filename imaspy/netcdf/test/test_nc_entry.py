import pytest

from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT
from imaspy.ids_factory import IDSFactory
from imaspy.netcdf.nc_entry import NCEntry


def test_readwrite(tmp_path):
    fname = tmp_path / "test-rw.nc"
    ids = IDSFactory().core_profiles()
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT

    with pytest.raises(FileNotFoundError):
        NCEntry(fname, "r")  # File does not exist
    with NCEntry(fname, "x") as entry:
        entry.put(ids)
    with NCEntry(fname, "w") as entry:
        with pytest.raises(KeyError):  # FIXME: change error class
            entry.get("core_profiles")  # File overwritten, IDS does not exist
        entry.put(ids)
    with pytest.raises(OSError):
        NCEntry(fname, "x")  # file already exists
    with NCEntry(fname, "a") as entry:
        with pytest.raises(RuntimeError):  # FIXME: change error class
            entry.put(ids)  # Cannot overwrite existing IDS
        # But we can write a new occurrence
        entry.put(ids, 1)
