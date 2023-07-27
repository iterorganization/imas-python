# Unit tests for ids_convert.py.
# See also integration tests for conversions in test_nbc_change.py

from unittest.mock import MagicMock

import pytest

from imaspy.db_entry import _get_timebasepath
from imaspy.ids_convert import (
    dd_version_map_from_factories,
    _get_ctxpath,
    _get_tbp,
)
from imaspy.ids_defs import IDS_TIME_MODE_HETEROGENEOUS
from imaspy.ids_factory import IDSFactory
from imaspy.ids_struct_array import IDSStructArray
from imaspy.ids_structure import IDSStructure


def test_dd_version_map_from_factories_invalid_version():
    factory1 = IDSFactory(version="3.39.0")
    factory2 = MagicMock()
    factory2._version = "3.30.0-123-12345678"
    factory2._etree = factory1._etree

    version_map, factory1_is_oldest = dd_version_map_from_factories(
        "core_profiles", factory1, factory2
    )
    assert not factory1_is_oldest
    # maps should be empty, since we set the same etree on factory2
    assert not version_map.new_to_old.path
    assert not version_map.old_to_new.path


@pytest.fixture()
def factory():
    return IDSFactory(version="3.38.0")


@pytest.fixture()
def core_profiles_paths(factory):
    etree = factory._etree
    cp = etree.find("IDS[@name='core_profiles']")
    return {field.get("path", ""): field for field in cp.iterfind(".//field")}


def test_aos_and_ctxpath(core_profiles_paths):
    paths = core_profiles_paths
    f = _get_ctxpath
    assert f("time", paths) == "time"
    assert f("profiles_1d", paths) == "profiles_1d"
    assert f("profiles_1d/time", paths) == "time"
    assert f("profiles_1d/grid/rho_tor_norm", paths) == "grid/rho_tor_norm"
    assert f("profiles_1d/ion", paths) == "ion"
    assert f("profiles_1d/ion/element", paths) == "element"
    assert f("profiles_1d/ion/element/z_n", paths) == "z_n"


def test_timebasepath(core_profiles_paths):
    paths = core_profiles_paths
    f = _get_tbp
    assert f(paths["time"], paths) == "time"
    assert f(paths["profiles_1d"], paths) == "profiles_1d/time"
    assert f(paths["profiles_1d/grid"], paths) == ""


def test_compare_timebasepath_functions(ids_name):
    # Ensure that the two timebasepath implementations are consistent
    ids = IDSFactory().new(ids_name)
    ids_element = ids._structure_xml
    paths = {field.get("path", ""): field for field in ids_element.iterfind(".//field")}

    def recurse(structure: IDSStructure, ctx_path: str):
        for item in structure:
            name = item.metadata.name
            new_path = f"{ctx_path}/{name}" if ctx_path else name

            tbp1 = _get_tbp(item._structure_xml, paths)
            tbp2 = _get_timebasepath(item, IDS_TIME_MODE_HETEROGENEOUS, new_path)
            assert tbp1 == tbp2

            if isinstance(item, IDSStructure):
                recurse(item, new_path)
            else:
                if isinstance(item, IDSStructArray):
                    item.resize(1)
                    recurse(item[0], "")

    recurse(ids, "")
