""" Print out tag information contained in given DD XML
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from pprint import pprint
from functools import reduce


def parse_element(element: ET.Element):
    if element.tag == "field":
        dtype = element.attrib.get("data_type", None)
        summary.setdefault(dtype, set()).add(frozenset(element.attrib))
    else:
        ignored_tags.add(element.tag)
    for child in element:
        parse_element(child)


if __name__ == "__main__":
    # Parse user arguments
    if len(sys.argv) > 1:
        xml_path = Path(sys.argv[1])
    else:
        xml_path = Path("IDSDef.xml")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    summary = {}
    ignored_tags = set()

    # Parse tree
    parse_element(root)

    # Always print pretty, overwrites build-ins, I know
    print = pprint

    print("Ignored tags:")
    print(ignored_tags)

    print("Summary:")

    for dtype in summary:
        print(f"Data type: {dtype}")
        print(reduce(set.union, summary[dtype], set()))

    print("All:")
    print(
        reduce(
            set.union, (reduce(set.union, value, set()) for value in summary.values())
        )
    )
