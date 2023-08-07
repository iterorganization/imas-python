# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

import pprint

import pytest

from imaspy.ids_mixin import IDSMixin
from imaspy.ids_structure import IDSStructure
from imaspy.ids_toplevel import IDSToplevel


class fake_parent_factory:
    pass


class fake_array_parent:
    _path = "/fake/parent"


@pytest.fixture
def mixin(fake_structure_xml):
    wavevector_xml = fake_structure_xml.find(".//*[@name='wavevector']")
    fake_structure_xml.remove(wavevector_xml)
    top = IDSToplevel(
        fake_parent_factory,
        fake_structure_xml,
    )
    mixin = IDSMixin(top, wavevector_xml)
    return mixin


def test_time_mode(mixin):
    assert mixin._time_mode == -999999999


def test_toplevel(fake_filled_toplevel):
    top = fake_filled_toplevel
    assert top.wavevector._toplevel == top
    assert top.wavevector[0].radial_component_norm._toplevel == top


def test_path(fake_filled_toplevel):
    top = fake_filled_toplevel
    assert top.wavevector._path == "wavevector"
    assert top.ids_properties.creation_date._path == "ids_properties/creation_date"
    assert top.wavevector._path == "wavevector"
    assert top.wavevector[0]._path == "wavevector[0]"
    assert (
        top.wavevector[0].radial_component_norm._path
        == "wavevector[0]/radial_component_norm"
    )
