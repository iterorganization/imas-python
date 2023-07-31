# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
from pathlib import Path
import pytest
import pprint

from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test.test_helpers import open_dbentry

# As the IDSPrimitive class generally should not be used on its own. Instead we
# take a very well defined toplevel, initialize it, and do our tests on the
# tree structure that is generated. Keep the tests just to the functionality
# that is defined in ids_primitive.py though!


@pytest.fixture
def toplevel(fake_toplevel_xml: Path, worker_id: str, tmp_path: Path):
    """A toplevel where specific fields are filled"""
    dbentry = open_dbentry(
        MEMORY_BACKEND, "w", worker_id, tmp_path, xml_path=fake_toplevel_xml
    )
    # Take a small toplevel and partially fill it with very specific fields
    top = dbentry.factory.new("gyrokinetics")
    top.wavevector.resize(1)
    top.wavevector[0].eigenmode.resize(1)
    eig = top.wavevector[0].eigenmode[0]
    eig.frequency_norm = 10
    top.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    dbentry.put(top)

    yield dbentry.get("gyrokinetics")

    dbentry.close()


def test_pretty_print(toplevel):
    assert pprint.pformat(toplevel).startswith("<imaspy.ids_toplevel.IDSToplevel")
    assert pprint.pformat(toplevel.wavevector[0].eigenmode).startswith(
        "<imaspy.ids_struct_array.IDSStructArray"
    )
    assert pprint.pformat(toplevel.wavevector[0].eigenmode[0]).startswith(
        "<imaspy.ids_structure.IDSStructure"
    )
