from copy import deepcopy

import pytest

from imaspy.dd_zip import dd_etree
from imaspy.ids_toplevel import IDSToplevel
from imaspy.ids_metadata import IDSMetadata


@pytest.fixture
def fake_structure_xml(fake_toplevel_xml):
    tree = dd_etree(version=None, xml_path=fake_toplevel_xml)
    return tree.find("IDS")


def test_metadata_init():
    meta = IDSMetadata()
    # maxoccur should always be defined
    assert meta.maxoccur is None


def test_metadata_init_structure_xml(fake_structure_xml):
    meta = IDSMetadata(structure_xml=fake_structure_xml)
    assert fake_structure_xml.attrib["name"] == "gyrokinetics"
    assert meta["name"] == "gyrokinetics"
    assert meta.name == "gyrokinetics"


def test_deepcopy(fake_structure_xml):
    meta = IDSMetadata(structure_xml=fake_structure_xml)
    meta2 = deepcopy(meta)

    # Test that a new but equivalent IDSMetadata instance is created
    assert meta is not meta2
    assert meta == meta2

    # Test that its indeed separated
    meta2.name = "blergh"
    assert meta.name != meta2.name
