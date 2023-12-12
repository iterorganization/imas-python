from copy import deepcopy

import pytest

from imaspy.ids_metadata import IDSType, get_toplevel_metadata


def test_metadata_cache(fake_structure_xml):
    meta = get_toplevel_metadata(fake_structure_xml)
    meta2 = get_toplevel_metadata(fake_structure_xml)
    assert meta is meta2


def test_metadata_init_structure_xml(fake_structure_xml):
    meta = get_toplevel_metadata(fake_structure_xml)
    assert fake_structure_xml.attrib["name"] == "gyrokinetics"
    assert meta.name == "gyrokinetics"


def test_metadata_deepcopy(fake_structure_xml):
    meta = get_toplevel_metadata(fake_structure_xml)
    meta2 = deepcopy(meta)

    # Test that deepcopy returns the same reference
    assert meta is meta2
    assert meta == meta2


def test_metadata_immutable(fake_structure_xml):
    meta = get_toplevel_metadata(fake_structure_xml)
    with pytest.raises(RuntimeError):
        meta.immutable = True


def test_ids_type():
    assert not IDSType.NONE.is_dynamic
    assert not IDSType.CONSTANT.is_dynamic
    assert not IDSType.STATIC.is_dynamic
    assert IDSType.DYNAMIC.is_dynamic
