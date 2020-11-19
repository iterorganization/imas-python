# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging

from . import imaspy

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)


def test_load_minimal():
    ids = imaspy.ids_classes.IDSRoot(
        0, 0, xml_path="assets/IDS_minimal.xml", verbosity=2
    )  # Create a empty IDSs

    # Check if the datatypes are loaded correctly
    assert ids.minimal.a.data_type == "FLT_0D"
    assert ids.minimal.ids_properties.comment.data_type == "STR_0D"

    # Check the documentation
    # assert ids.minimal.a.documentation == "A float"
    # assert ids.minimal.ids_properties.documentation == "Properties of this IDS"
    # assert ids.minimal.ids_properties.comment.documentation == "A string comment"

    # Check the units
    # assert ids.minimal.a.units == "unitless"

    # Check the static/dynamic/constant annotation
    # assert ids.minimal.a.type == "static"
    # assert ids.minimal.ids_properties.comment.type == "constant"


def test_load_multiple_minimal():
    ids = imaspy.ids_classes.IDSRoot(
        0, 0, xml_path="assets/IDS_minimal.xml", verbosity=2
    )  # Create a empty IDSs

    # Check if the datatypes are loaded correctly
    assert ids.minimal.a.data_type == "FLT_0D"
    assert ids.minimal.ids_properties.comment.data_type == "STR_0D"

    ids2 = imaspy.ids_classes.IDSRoot(
        0, 0, xml_path="assets/IDS_minimal.xml", verbosity=2
    )  # Create a empty IDSs

    # Check if the datatypes are loaded correctly
    assert ids2.minimal.a.data_type == "FLT_0D"
    assert ids2.minimal.ids_properties.comment.data_type == "STR_0D"
