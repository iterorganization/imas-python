import pytest

from imaspy.netcdf.nc_entry import NCEntry
from imaspy.test.test_helpers import compare_children, fill_consistent


def test_nc_latest_dd_autofill_put_get(ids_name, tmp_path):
    if ids_name == "amns_data":
        pytest.skip(reason="amns_data not supported for fill_consistent")

    nc_entry = NCEntry(f"{tmp_path}/test-{ids_name}.nc", "x", diskless=True)
    ids = nc_entry.factory.new(ids_name)
    fill_consistent(ids, 0.5)

    nc_entry.put(ids)
    ids2 = nc_entry.get(ids_name)

    compare_children(ids, ids2)
