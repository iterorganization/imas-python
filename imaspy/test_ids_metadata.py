import pytest

from imaspy.dd_zip import dd_etree
from imaspy.ids_toplevel import IDSToplevel
from imaspy.ids_metadata import IDSMetadata


def test_metadata_init():
    meta = IDSMetadata()
    # maxoccur should always be defined
    assert meta.maxoccur is None


def test_metadata_init_structure_xml(fake_toplevel_xml):
    tree = dd_etree(version=None, xml_path=fake_toplevel_xml)
    ids = tree.find("IDS")
    meta = IDSMetadata(structure_xml=ids)
    assert ids.attrib["name"] == "gyrokinetics"
