from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier, Event

import pytest

from imas import ids_metadata
from imas.ids_factory import IDSFactory
from imas.ids_metadata import IDSMetadata, IDSType, get_toplevel_metadata
from imas.util import idsdiffgen


def test_metadata_cache(fake_structure_xml):
    meta = get_toplevel_metadata(fake_structure_xml)
    meta2 = get_toplevel_metadata(fake_structure_xml)
    assert meta is meta2


def test_metadata_init_structure_xml(fake_structure_xml):
    meta = get_toplevel_metadata(fake_structure_xml)
    assert fake_structure_xml.attrib["name"] == "gyrokinetics"
    assert meta.name == "gyrokinetics"


def test_metadata_deepcopy(fake_structure_xml):
    meta = get_toplevel_metadata(fake_structure_xml)
    meta2 = deepcopy(meta)

    # Test that deepcopy returns the same reference
    assert meta is meta2
    assert meta == meta2


def test_metadata_immutable(fake_structure_xml):
    meta = get_toplevel_metadata(fake_structure_xml)
    with pytest.raises(RuntimeError):
        meta.immutable = True
    with pytest.raises(RuntimeError):
        del meta.name


def assert_metadata_immutable(meta):
    for node in (meta, meta["ids_properties"], meta["ids_properties/comment"]):
        with pytest.raises(RuntimeError, match="IDSMetadata is read-only"):
            node.name = node.name
        with pytest.raises(RuntimeError, match="IDSMetadata is read-only"):
            node.new_attribute = True
        with pytest.raises(RuntimeError, match="IDSMetadata is read-only"):
            del node.name


@pytest.fixture
def paused_metadata_init(monkeypatch):
    """Pause the first build at a child node, with bounded waits and cleanup."""
    factory = IDSFactory("3.39.0")
    # Fresh XML elements ensure cache misses regardless of test order.
    factory._ids_elements = {
        name: deepcopy(factory._ids_elements[name])
        for name in ("core_profiles", "equilibrium")
    }
    first_child = factory._ids_elements["core_profiles"][0]
    entered = Event()
    resume = Event()
    original_init = IDSMetadata.__init__
    original_setattr = IDSMetadata.__setattr__

    def init(self, structure_xml, context_path, parent_meta):
        if structure_xml is first_child and not entered.is_set():
            entered.set()
            assert resume.wait(10), "Metadata construction was not resumed"
        original_init(self, structure_xml, context_path, parent_meta)

    # Restore the class even when running this regression against the old code.
    monkeypatch.setattr(IDSMetadata, "__setattr__", original_setattr)
    monkeypatch.setattr(IDSMetadata, "__init__", init)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(factory.core_profiles)
        try:
            assert entered.wait(10), "Metadata construction did not reach a child"
            yield factory, executor, first, resume
        finally:
            resume.set()


@pytest.mark.parametrize("second_name", ["equilibrium", "core_profiles"])
def test_concurrent_metadata_construction(paused_metadata_init, second_name):
    factory, executor, first, resume = paused_metadata_init
    second = executor.submit(factory.new, second_name).result(timeout=10)
    assert second.metadata.name == second_name
    assert_metadata_immutable(second.metadata)
    resume.set()
    first = first.result(timeout=10)
    assert first.metadata.name == "core_profiles"
    assert_metadata_immutable(first.metadata)
    assert_metadata_immutable(second.metadata)


def test_metadata_immutable_during_construction(fake_structure_xml, monkeypatch):
    existing = get_toplevel_metadata(fake_structure_xml)
    entered = Event()
    resume = Event()
    original_init = IDSMetadata.__init__

    def init(self, structure_xml, context_path, parent_meta):
        if parent_meta is None:
            entered.set()
            assert resume.wait(10), "Metadata construction was not resumed"
        original_init(self, structure_xml, context_path, parent_meta)

    monkeypatch.setattr(IDSMetadata, "__init__", init)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(get_toplevel_metadata, deepcopy(fake_structure_xml))
        try:
            assert entered.wait(10), "Metadata construction did not start"
            assert_metadata_immutable(existing)
        finally:
            resume.set()
        assert_metadata_immutable(future.result(timeout=10))
    assert_metadata_immutable(existing)


def test_metadata_failed_construction(fake_structure_xml):
    existing = get_toplevel_metadata(deepcopy(fake_structure_xml))
    child = fake_structure_xml[0]
    child.set("maxoccur", "invalid")
    with pytest.raises(ValueError):
        get_toplevel_metadata(fake_structure_xml)
    assert_metadata_immutable(existing)
    del child.attrib["maxoccur"]
    assert_metadata_immutable(get_toplevel_metadata(fake_structure_xml))


def test_concurrent_metadata_type_map_initialization(fake_structure_xml, monkeypatch):
    entered = Event()
    resume = Event()

    def paused_range(*args):
        # Stop before the numeric array types are added to the table.
        if args == (1, 7) and not entered.is_set():
            entered.set()
            assert resume.wait(10), "Type map initialization was not resumed"
        return range(*args)

    monkeypatch.setattr(ids_metadata, "_type_map", {})
    monkeypatch.setattr(ids_metadata, "range", paused_range, raising=False)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(get_toplevel_metadata, fake_structure_xml)
        try:
            assert entered.wait(10), "Type map initialization did not start"
            second = executor.submit(
                get_toplevel_metadata, deepcopy(fake_structure_xml)
            ).result(timeout=10)
        finally:
            resume.set()
        assert_metadata_immutable(first.result(timeout=10))
    assert_metadata_immutable(second)


@pytest.mark.parametrize("version, ion_name", [("3.39.0", "label"), ("4.0.0", "name")])
def test_independent_ids_filled_concurrently(version, ion_name):
    workers = 4
    barrier = Barrier(workers, timeout=10)

    def fill(index, parallel=False):
        if parallel:
            barrier.wait()
        ids = IDSFactory(version).core_profiles()
        ids.ids_properties.homogeneous_time = 1
        ids.ids_properties.comment = f"Independent IDS {index}"
        ids.time = [0.0, 1.0]
        ids.profiles_1d.resize(2)
        for profile in ids.profiles_1d:
            profile.grid.rho_tor_norm = [0.0, 0.5, 1.0]
            profile.electrons.temperature = [index + 1.0, index + 2.0, index + 3.0]
            profile.ion.resize(1)
            setattr(profile.ion[0], ion_name, f"D{index}")
            profile.ion[0].density = [index + 4.0, index + 5.0, index + 6.0]
        ids.validate()
        return ids

    expected = [fill(index) for index in range(workers)]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fill, index, True) for index in range(workers)]
        actual = [future.result(timeout=10) for future in futures]
    for serial, parallel in zip(expected, actual):
        assert list(idsdiffgen(serial, parallel)) == []
        assert_metadata_immutable(parallel.metadata)


def test_ids_type():
    assert not IDSType.NONE.is_dynamic
    assert not IDSType.CONSTANT.is_dynamic
    assert not IDSType.STATIC.is_dynamic
    assert IDSType.DYNAMIC.is_dynamic


def test_metadata_indexing():
    core_profiles = IDSFactory("3.39.0").core_profiles()
    metadata = core_profiles.metadata
    assert metadata["ids_properties"] is core_profiles.ids_properties.metadata
    assert (
        metadata["ids_properties/version_put"]
        is core_profiles.ids_properties.version_put.metadata
    )
    assert metadata["time"] is core_profiles.time.metadata
    p1d_time_meta = metadata["profiles_1d/time"]
    core_profiles.profiles_1d.resize(1)
    assert p1d_time_meta is core_profiles.profiles_1d[0].time.metadata

    # Test period (.) as separator:
    assert (
        metadata["profiles_1d/electrons/temperature"]
        is metadata["profiles_1d.electrons.temperature"]
    )

    # Test invalid path
    with pytest.raises(KeyError):
        metadata["DoesNotExist"]
