# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging

import imaspy

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)


def test_load_minimal_types():
    ids = imaspy.ids_classes.IDSRoot(
        0, 0, xml_path="assets/IDS_minimal_types.xml", verbosity=2
    )  # Create a empty IDSs

    # Check if the datatypes are loaded correctly
    assert ids.minimal.a.data_type == "FLT_0D"
    assert ids.minimal.ids_properties.comment.data_type == "STR_0D"
