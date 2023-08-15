# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
import pprint

import pytest

from imaspy.ids_structure import IDSStructure


@pytest.fixture
def structure(fake_filled_toplevel) -> IDSStructure:
    yield fake_filled_toplevel.ids_properties


def test_pretty_print(structure):
    assert (
        pprint.pformat(structure) == "<IDSStructure (IDS:gyrokinetics, ids_properties)>"
    )
