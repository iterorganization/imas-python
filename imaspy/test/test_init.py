# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
import imaspy


def test_access_layer_version_version():
    assert isinstance(imaspy.__version__, str)
