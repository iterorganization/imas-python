import pytest

from imaspy.dd_zip import dd_xml_versions
from imaspy.ids_factory import IDSFactory
from imaspy.test.test_helpers import fill_with_random_data


@pytest.fixture(params=dd_xml_versions())
def dd_version(request):
    return request.param


@pytest.mark.slow
def test_autofill_dd_version(dd_version):
    factory = IDSFactory(version=dd_version)
    for ids_name in factory:
        fill_with_random_data(factory.new(ids_name), max_children=1)
