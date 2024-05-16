import pytest

from imaspy.ids_data_type import IDSDataType
from imaspy.netcdf.nc_entry import NCEntry
from imaspy.test.test_helpers import compare_children, fill_consistent
from imaspy.util import tree_iter


def test_nc_latest_dd_autofill_put_get(ids_name, tmp_path):
    if ids_name == "amns_data":
        pytest.skip(reason="amns_data not supported for fill_consistent")

    nc_entry = NCEntry(f"{tmp_path}/test-{ids_name}.nc", "x", diskless=True)
    ids = nc_entry.factory.new(ids_name)
    fill_consistent(ids, 0.5)

    # Delete complex-valued variables
    for var in tree_iter(ids):
        if var.metadata.data_type is IDSDataType.CPX:
            delattr(var._parent, var.metadata.name)
    # TODO: add support for complex numbers

    nc_entry.put(ids)
    ids2 = nc_entry.get(ids_name)

    compare_children(ids, ids2)
