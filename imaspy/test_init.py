import pytest
import types
import imaspy


def test_access_layer_version():
    def test_access_layer_version_version():
        assert isinstance(imaspy.__version__, str)

    @pytest.mark.xfail
    def test_expected_fail():
        assert False

    @pytest.mark.xfail
    def test_unexpected_pass():
        assert True
