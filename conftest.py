# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
#
# Set up pytest so that any mention of 'backend' as a test argument
# gets run with all four backends.
# Same for ids_type, with all types
import pytest

from imaspy.dd_zip import dd_xml_versions, latest_dd_version
from imaspy.ids_defs import ASCII_BACKEND, HDF5_BACKEND, MDSPLUS_BACKEND, MEMORY_BACKEND
from imaspy.ids_root import IDSRoot
from imaspy.test_minimal_types_io import TEST_DATA


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


def pytest_generate_tests(metafunc):
    if "backend" in metafunc.fixturenames:
        all = True
        if metafunc.config.getoption("ascii"):
            metafunc.parametrize("backend", [ASCII_BACKEND])
            all = False
        if metafunc.config.getoption("memory"):
            metafunc.parametrize("backend", [MEMORY_BACKEND])
            all = False
        if metafunc.config.getoption("hdf5"):
            metafunc.parametrize("backend", [HDF5_BACKEND])
            all = False
        if metafunc.config.getoption("mdsplus"):
            metafunc.parametrize("backend", [MDSPLUS_BACKEND])
            all = False
        if all:
            metafunc.parametrize(
                "backend",
                # Do not test with HDF5 backend for now, it is not done
                [MEMORY_BACKEND, ASCII_BACKEND, MDSPLUS_BACKEND],
            )
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
    from pathlib import Path

    return Path(__file__).parent / "imaspy/assets/IDS_fake_toplevel.xml"

@pytest.fixture
def ids_minimal():
    from pathlib import Path

    return Path(__file__).parent / "imaspy/assets/IDS_minimal.xml"


@pytest.fixture
def ids_minimal_types():
    from pathlib import Path

    return Path(__file__).parent / "imaspy/assets/IDS_minimal_types.xml"
