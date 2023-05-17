# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
#
# Set up pytest so that any mention of 'backend' as a test argument
# gets run with all four backends.
# Same for ids_type, with all types
import importlib_resources
import pytest

from imaspy.ids_defs import ASCII_BACKEND, HDF5_BACKEND, MDSPLUS_BACKEND, MEMORY_BACKEND
from imaspy.ids_root import IDSRoot

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


# Fixtures for various assets
@pytest.fixture(scope="session")
def imaspy_assets():
    return importlib_resources.files("imaspy") / "assets"


@pytest.fixture(scope="session")
def fake_toplevel_xml(imaspy_assets):
    return imaspy_assets / "IDS_fake_toplevel.xml"


@pytest.fixture(scope="session")
def ids_minimal(imaspy_assets):
    return imaspy_assets / "IDS_minimal.xml"


@pytest.fixture(scope="session")
def ids_minimal2(imaspy_assets):
    return imaspy_assets / "IDS_minimal_2.xml"


@pytest.fixture(scope="session")
def ids_minimal_struct_array(imaspy_assets):
    return imaspy_assets / "IDS_minimal_struct_array.xml"


@pytest.fixture(scope="session")
def ids_minimal_types(imaspy_assets):
    return imaspy_assets / "IDS_minimal_types.xml"
