# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
from copy import deepcopy
import pprint

import pytest

from imaspy.ids_toplevel import IDSToplevel
from imaspy.ids_structure import IDSStructure


class fake_parent_factory:
    _path = ""


@pytest.fixture
def structure(fake_structure_xml):
    ids_properties_xml = fake_structure_xml.find(".//*[@name='ids_properties']")
    fake_structure_xml.remove(ids_properties_xml)
    top = IDSToplevel(
        fake_parent_factory,
        fake_structure_xml,
    )
    structure = IDSStructure(top, ids_properties_xml)
    return structure


def test_pretty_print(structure):
    assert (
        pprint.pformat(structure) == "<IDSStructure (IDS:gyrokinetics, ids_properties)>"
    )
