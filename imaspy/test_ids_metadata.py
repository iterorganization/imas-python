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


def test_deepcopy(fake_structure_xml):
    meta = IDSMetadata(structure_xml=fake_structure_xml)
    meta2 = deepcopy(meta)
    assert meta is not meta2
    # assert meta.maxoccur is not meta2.maxoccur
    assert meta == meta2
