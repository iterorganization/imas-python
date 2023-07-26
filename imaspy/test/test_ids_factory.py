import pytest

from imaspy.dd_zip import dd_etree, latest_dd_version
from imaspy.ids_factory import IDSFactory


def test_ids_factory_with_version():
    IDSFactory(version="3.38.1")


def test_ids_factory_with_invalid_version():
    # This raises a packaging.version.InvalidVersion exception, but any exception is ok
    with pytest.raises(Exception):
        IDSFactory(version="invalid")
    # This is a valid version string, but we don't have it available
    with pytest.raises(ValueError):
        IDSFactory(version="0.1.2.3.4")


def test_ids_factory_with_xml_path(ids_minimal):
    IDSFactory(xml_path=ids_minimal)


def test_ids_factory_latest(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("IMAS_VERSION", raising=False)
    monkeypatch.delenv("IMAS_PREFIX", raising=False)
    dd_etree.cache_clear()
    factory = IDSFactory()
    assert factory._version == latest_dd_version()
    dd_etree.cache_clear()


def test_ids_factory_from_env(monkeypatch: pytest.MonkeyPatch):
    version = "3.35.0"
    monkeypatch.setenv("IMAS_VERSION", version)
    dd_etree.cache_clear()
    factory = IDSFactory()
    assert factory._version == version
    dd_etree.cache_clear()