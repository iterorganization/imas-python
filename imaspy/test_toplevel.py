"""A testcase checking if higher-level IDSToplevel features with a fake
constant-in-time DD
"""
from pathlib import Path

import pytest

from imaspy.dd_zip import dd_etree
from imaspy.ids_toplevel import IDSToplevel


@pytest.fixture
def prepped_tree(toplevel_xml: Path):
    # Copy nessecary IDSRoot logic in here to create a toplevel
    # This is basically a simplified and specialized IDSRoot.__init__
    # TODO: clean unnessecary variables
    shot = 7
    run = 3
    rs = None
    rr = None

    # The following attributes relate to the UAL-LL
    treeName = "ids"
    connected = False
    expIdx = -1

    ver = "0.0.1"
    _xml_path = toplevel_xml
    _tree = dd_etree(version=ver, xml_path=_xml_path)

    _backend_version = None
    _backend_xml_path = None

    # Parse given xml_path and build imaspy IDS structures
    _children = []

    _imas_version = None
    for ids in _tree.getroot():
        my_name = ids.get("name")
        if my_name is None:
            # This means it is not an IDS, maybe some other tag?
            # TODO: Find edge cases
            # One such case is "version"
            if ids.tag == "version":
                _imas_version = ids.text
                continue
            elif ids.tag == "cocos":
                cocos = int(ids.text)
                continue
            elif ids.tag == "utilities":
                # TODO: What to do with utilities?
                utilities_text = ids.text.strip()
                continue
            else:
                raise Exception("Unhandled 'my_name is None' case")
        if my_name == "version":
            # print("Found XML version %s", ids.text)
            _imas_version = ids.text
        else:
            # print(f"{my_name} tree init, found toplevel")
            toplevel = IDSToplevel(
                object(),
                my_name,
                ids,
                backend_version=_backend_version,
                backend_xml_path=_backend_xml_path,
            )
        _children.append(my_name)
    assert _imas_version == ver
    assert "gyrokinetics" in _children
    assert len(_children) == 1
    yield _children[0], toplevel


def test_toplevel_init(prepped_tree):
    name, ids = prepped_tree
    # Test fundamental assumptions and fixture for next tests
    assert isinstance(ids, IDSToplevel)
    assert isinstance(name, str)
