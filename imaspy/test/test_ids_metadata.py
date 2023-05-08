from copy import deepcopy

import pytest

from imaspy.dd_zip import dd_etree
from imaspy.ids_metadata import IDSMetadata


@pytest.fixture
def fake_structure_xml(fake_toplevel_xml):
    tree = dd_etree(version=None, xml_path=fake_toplevel_xml)
    return tree.find("IDS")


def test_metadata_cache(fake_structure_xml):
    meta = IDSMetadata(structure_xml=fake_structure_xml)
    meta2 = IDSMetadata(structure_xml=fake_structure_xml)
    assert meta is meta2


def test_metadata_init_structure_xml(fake_structure_xml):
    meta = IDSMetadata(structure_xml=fake_structure_xml)
    assert fake_structure_xml.attrib["name"] == "gyrokinetics"
    assert meta.name == "gyrokinetics"


def test_metadata_deepcopy(fake_structure_xml):
    meta = IDSMetadata(structure_xml=fake_structure_xml)
    meta2 = deepcopy(meta)

    # Test that deepcopy returns the same reference
    assert meta is meta2
    assert meta == meta2


def test_metadata_immutable(fake_structure_xml):
    meta = IDSMetadata(fake_structure_xml)
    with pytest.raises(RuntimeError):
        meta.immutable = True
