import pytest

from imaspy.db_entry import DBEntry
from imaspy.test.test_helpers import compare_children, fill_consistent


def test_nc_latest_dd_autofill_put_get(ids_name, tmp_path):
    if ids_name == "amns_data":
        pytest.skip(reason="amns_data not supported for fill_consistent")

    with DBEntry(f"{tmp_path}/test-{ids_name}.nc", "x") as entry:
        ids = entry.factory.new(ids_name)
        fill_consistent(ids, 0.5)

        entry.put(ids)
        ids2 = entry.get(ids_name)

    compare_children(ids, ids2)
