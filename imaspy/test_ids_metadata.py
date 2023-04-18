import pytest

from imaspy.ids_toplevel import IDSToplevel
from imaspy.ids_metadata import IDSMetadata


def test_metadata_init():
    meta = IDSMetadata()
    # maxoccur should always be defined
    assert meta.maxoccur is None
