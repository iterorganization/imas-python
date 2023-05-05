import pytest

from imaspy.dd_zip import dd_xml_versions
from imaspy.ids_root import IDSRoot
from imaspy.test_helpers import fill_with_random_data


@pytest.fixture(params=dd_xml_versions())
def dd_version(request):
    return request.param


@pytest.mark.slow
def test_autofill_dd_version(dd_version):
    root = IDSRoot(version=dd_version)
    for ids in root:
        fill_with_random_data(ids, max_children=1)
