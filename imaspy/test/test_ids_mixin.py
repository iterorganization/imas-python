# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

import pprint

import pytest

from imaspy.ids_mixin import IDSMixin
from imaspy.ids_structure import IDSStructure
from imaspy.ids_toplevel import IDSToplevel


class fake_parent_factory:
    _path = ""


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


def test_parentless_path(fake_filled_toplevel):
    top = fake_filled_toplevel
    delattr(fake_filled_toplevel.wavevector[0].eigenmode, "_parent")
    # As we deleted the _parent, a lot magic can possibly break
    # We still want repr and thus _path to work though
    # In this use-case, the node "wavevector[0]" acts like it is an
    # IDSToplevel and should thus not be returned
    assert top.wavevector[0].eigenmode._path == "eigenmode"
    assert top.wavevector[0].eigenmode[0]._path == "eigenmode[0]"
    assert (
        top.wavevector[0].eigenmode[0].frequency_norm._path
        == "eigenmode[0]/frequency_norm"
    )
    # The ones that still have the parent should still act as expected
    assert (
        top.wavevector[0].radial_component_norm._path
        == "wavevector[0]/radial_component_norm"
    )
    assert top.wavevector[0]._path == "wavevector[0]"
    assert top.ids_properties.creation_date._path == "ids_properties/creation_date"


def test_unlinked_struct(fake_filled_toplevel):
    top = fake_filled_toplevel
    struct = top.wavevector[0]
    assert isinstance(struct, IDSStructure)
    struct._parent = fake_array_parent
    struct._parent.value = []
    # with pytest.raises(NotImplementedError) as excinfo:
    # In this case, the user has managed to mangle the IMASPy structure so
    # much, that a parent got unlinked with the parent structures.
    # Best-effort is to raise a better error than normally.
    # TODO: Investigate if we want (to support) this case
    assert struct.eigenmode._path == "eigenmode"
