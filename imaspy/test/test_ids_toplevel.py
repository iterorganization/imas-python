"""A testcase checking higher-level IDSToplevel features with a fake
constant-in-time DD
"""
from pathlib import Path

import pytest

from imaspy.ids_toplevel import IDSToplevel
from imaspy.ids_root import IDSRoot


@pytest.fixture
def prepped_tree(fake_toplevel_xml: Path):
    root = IDSRoot(xml_path=fake_toplevel_xml)
    yield root._children[0], root.gyrokinetics


def test_toplevel_init(prepped_tree):
    name, ids = prepped_tree
    # Test fundamental assumptions and fixture for next tests
    assert isinstance(ids, IDSToplevel)
    assert isinstance(name, str)


def test_structure_xml_noncopy(prepped_tree):
    name, ids = prepped_tree
    assert id(ids._structure_xml.getchildren()[0].attrib) == id(
        ids.ids_properties._structure_xml.attrib
    )


def test_metadata_lifecycle_status(prepped_tree):
    name, ids = prepped_tree
    assert ids.metadata.lifecycle_status == "alpha"
    assert ids.wavevector.metadata.structure_reference == "gyrokinetics_wavevector"


def test_metadata_non_exist(prepped_tree):
    name, ids = prepped_tree
    with pytest.raises(AttributeError):
        ids.wavevector.metadata.lifecycle_status


def test_metadata_attribute_not_exists(prepped_tree):
    name, ids = prepped_tree
    with pytest.raises(AttributeError):
        ids.metadata.blergh
