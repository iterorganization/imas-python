# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
from pathlib import Path
import pprint

import pytest


# As the IDSPrimitive class generally should not be used on its own. Instead we
# take a very well defined toplevel, initialize it, and do our tests on the
# tree structure that is generated. Keep the tests just to the functionality
# that is defined in ids_primitive.py though!


def test_pretty_print(fake_filled_toplevel):
    eig = fake_filled_toplevel.wavevector[0].eigenmode[0]
    assert pprint.pformat(eig.time_norm).startswith("<IDSNumericArray")
    assert pprint.pformat(eig.time_norm).endswith("\nnumpy.ndarray([], dtype=float64)")
    assert pprint.pformat(eig.frequency_norm).startswith("<IDSPrimitive")
    assert pprint.pformat(eig.frequency_norm).endswith("\nfloat(10.0)")
    fake_filled_toplevel.ids_properties.comment = "A filled comment"
    assert (
        pprint.pformat(fake_filled_toplevel.ids_properties.comment)
        == "<IDSPrimitive (IDS:gyrokinetics, ids_properties/comment, STR_0D)>\nstr('A filled comment')"
    )
