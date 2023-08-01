# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
from pathlib import Path
import pytest
import pprint

import numpy as np

from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test.test_helpers import open_dbentry
from imaspy.ids_primitive import *

# As the IDSPrimitive class generally should not be used on its own. Instead we
# take a very well defined toplevel, initialize it, and do our tests on the
# tree structure that is generated. Keep the tests just to the functionality
# that is defined in ids_primitive.py though!


zero_to_two_pi = np.linspace(0, 2, num=10) * np.pi


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
    eig.poloidal_angle = zero_to_two_pi
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
    eig = toplevel.wavevector[0].eigenmode[0]
    assert pprint.pformat(eig.time_norm).startswith("<IDSNumericArray")
    assert pprint.pformat(eig.time_norm).endswith("\nnumpy.ndarray([], dtype=float64)")
    assert pprint.pformat(eig.frequency_norm).startswith("<IDSPrimitive")
    assert pprint.pformat(eig.frequency_norm).endswith("\nfloat(10.0)")


def test_value_attribute(toplevel):
    """Test if the value attribute acts as IMASPy expects"""
    eig = toplevel.wavevector[0].eigenmode[0]
    assert isinstance(eig.frequency_norm, IDSPrimitive)
    assert hasattr(eig.frequency_norm, "value")

    # We should have a Python Primitive now:
    assert eig.frequency_norm.data_type == "FLT_0D"
    assert isinstance(eig.frequency_norm.value, float)
    assert eig.frequency_norm.value == 10

    # For arrays, we should get numpy arrays of the right type
    # This one should be not-filled, e.g. default
    assert not eig.phi_potential_perturbed_norm.has_value
    assert eig.phi_potential_perturbed_norm.data_type == "CPX_2D"
    assert isinstance(eig.phi_potential_perturbed_norm.value, np.ndarray)
    assert np.array_equal(eig.phi_potential_perturbed_norm.value, np.ndarray((0, 0)))

    # Finally, check a filled array
    assert eig.poloidal_angle.has_value
    assert eig.poloidal_angle.data_type == "FLT_1D"
    assert isinstance(eig.poloidal_angle.value, np.ndarray)
    assert np.array_equal(eig.poloidal_angle.value, zero_to_two_pi)


def test_visit_children(toplevel):
    # This should visit every node. Lets test that, but check only
    # filled fields explicitly
    eig = toplevel.wavevector[0].eigenmode[0]
    nodes = []
    toplevel.visit_children(lambda x: nodes.append(x) if x.has_value else None)
    # We know we filled only endpoints frequency_norm and poloidal_angle
    # We expect the following "mandatory" fields to be touched, which we check
    # the order visit_children visits
    assert len(nodes) == 12
    assert nodes[0] is toplevel
    assert nodes[1] is toplevel.ids_properties
    assert nodes[2] == 2
    assert nodes[3] is toplevel.ids_properties.version_put
    assert nodes[4] == "0.0.1"
    assert nodes[5] == "imaspy"
    assert nodes[6] is toplevel.wavevector
    assert nodes[7] is toplevel.wavevector[0]
    assert nodes[8] is toplevel.wavevector[0].eigenmode
    assert nodes[9] is toplevel.wavevector[0].eigenmode[0]
    assert nodes[10] == 10
    assert nodes[11] == zero_to_two_pi
