# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Extract DD versions from the provided zip file
"""
from pathlib import Path
from zipfile import ZipFile

ZIPFILE_LOCATION = Path(__file__).parent.parent / "data-dictionary" / "IDSDef.zip"


def get_dd_xml(version):
    """Given a version string, try to find {version}.xml in data-dictionary/IDSDef.zip
    and return the unzipped bytes"""
    try:
        with ZipFile(ZIPFILE_LOCATION, mode="r") as dd_zip:
            return dd_zip.read("data-dictionary/{version}.xml".format(version=version))
    except FileNotFoundError:
        raise FileNotFoundError("IMAS DD zipfile not found at {path}", ZIPFILE_LOCATION)
    except KeyError:
        raise FileNotFoundError(
            "IMAS DD version not found in data-dictionary/IDSDef.zip"
        )
