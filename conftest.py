# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
#
# Set up pytest so that any mention of 'backend' as a test argument
# gets run with all four backends.
# Same for ids_type, with all types
from pathlib import Path

import pytest

from imaspy.ids_defs import ASCII_BACKEND, HDF5_BACKEND, MDSPLUS_BACKEND, MEMORY_BACKEND
from imaspy.ids_root import IDSRoot
from imaspy.test_minimal_types_io import TEST_DATA

try:
    import imas
except ImportError:
    imas = None
_has_imas = imas is not None


def pytest_addoption(parser):
    # if none of these are specified, test with all backends
    parser.addoption("--mdsplus", action="store_true", help="test with MDSPlus backend")
    parser.addoption("--memory", action="store_true", help="test with memory backend")
    parser.addoption("--ascii", action="store_true", help="test with ascii backend")
    parser.addoption("--hdf5", action="store_true", help="test with HDF5 backend")
    parser.addoption("--mini", action="store_true", help="small test with few types")
    parser.addoption(
        "--ids", action="append", help="small test with few types", nargs="+"
    )


_BACKENDS = {
    "ascii": ASCII_BACKEND,
    "memory": MEMORY_BACKEND,
    "hdf5": HDF5_BACKEND,
    "mdsplus": MDSPLUS_BACKEND,
}


@pytest.fixture(scope="session", params=_BACKENDS)
def backend(pytestconfig: pytest.Config, request: pytest.FixtureRequest):
    backends_provided = any(map(pytestconfig.getoption, _BACKENDS))
    if not _has_imas:
        if backends_provided:
            raise RuntimeError(
                "Explicit backends are provided, but IMAS is not available."
            )
        pytest.skip("No IMAS available, skip tests using a backend")
    if backends_provided and not pytestconfig.getoption(request.param):
        pytest.skip(f"Tests for {request.param} backend are skipped.")
    return _BACKENDS[request.param]


@pytest.fixture(scope="session")
def has_imas():
    return _has_imas


@pytest.fixture(scope="session")
def requires_imas():
    if not _has_imas:
        pytest.skip("No IMAS available")


def pytest_generate_tests(metafunc):
    if "ids_type" in metafunc.fixturenames:
        if metafunc.config.getoption("mini"):
            metafunc.parametrize("ids_type", ["int_0d"])
        else:
            metafunc.parametrize("ids_type", [None] + list(TEST_DATA.keys()))

    if "ids_name" in metafunc.fixturenames:
        if metafunc.config.getoption("ids"):
            metafunc.parametrize(
                "ids_name",
                [
                    item
                    for arg in metafunc.config.getoption("ids")
                    for item in arg[0].split(",")
                ],
            )
        elif metafunc.config.getoption("mini"):
            metafunc.parametrize("ids_name", ["pulse_schedule"])
        else:
            metafunc.parametrize("ids_name", IDSRoot()._children)

    # Any variables ending with _bool will be set to both true and false
    for name in metafunc.fixturenames:
        if name.endswith("_bool"):
            metafunc.parametrize(name, [True, False])


@pytest.fixture
def fake_toplevel_xml():
    return Path(__file__).parent / "imaspy/assets/IDS_fake_toplevel.xml"


@pytest.fixture
def ids_minimal():
    return Path(__file__).parent / "imaspy/assets/IDS_minimal.xml"


@pytest.fixture
def ids_minimal_types():
    return Path(__file__).parent / "imaspy/assets/IDS_minimal_types.xml"
