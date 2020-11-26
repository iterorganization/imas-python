# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Extract DD versions from the provided zip file
"""
from distutils.version import StrictVersion
from pathlib import Path
from zipfile import ZipFile

from imas.logger import logger

ZIPFILE_LOCATION = Path(__file__).parent.parent / "data-dictionary" / "IDSDef.zip"


def get_dd_xml(version):
    """Given a version string, try to find {version}.xml in data-dictionary/IDSDef.zip
    and return the unzipped bytes"""
    if StrictVersion(version) < StrictVersion("3.22.0"):
        logger.warning(
            "Version {version} is below lowest supported version of 3.22.0. \
            Proceed at your own risk."
        )
    try:
        with ZipFile(ZIPFILE_LOCATION, mode="r") as dd_zip:
            return dd_zip.read("data-dictionary/{version}.xml".format(version=version))
    except FileNotFoundError:
        raise FileNotFoundError("IMAS DD zipfile not found at {path}", ZIPFILE_LOCATION)
    except KeyError:
        raise FileNotFoundError(
            "IMAS DD version not found in data-dictionary/IDSDef.zip"
        )


def dd_xml_versions():
    """Parse data-dictionary/IDSDef.zip to find version numbers available"""
    dd_prefix_len = len("data-dictionary/")
    try:
        with ZipFile(ZIPFILE_LOCATION, mode="r") as dd_zip:
            return sorted(
                [f[dd_prefix_len:-4] for f in dd_zip.namelist()], key=StrictVersion
            )
    except FileNotFoundError:
        raise FileNotFoundError("IMAS DD zipfile not found at {path}", ZIPFILE_LOCATION)
