# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Extract DD versions from the provided zip file
"""
import logging
from distutils.version import StrictVersion as V
from pathlib import Path
from zipfile import ZipFile

import imaspy

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.WARNING)

ZIPFILE_LOCATION = Path(__file__).parent.parent / "data-dictionary" / "IDSDef.zip"


def get_dd_xml(version):
    """Given a version string, try to find {version}.xml in data-dictionary/IDSDef.zip
    and return the unzipped bytes"""

    print_supported_version_warning(version)
    return safe_get(lambda dd_zip: dd_zip.read(fname(version)))


def get_dd_xml_crc(version):
    """Given a version string, try to find {version}.xml in data-dictionary/IDSDef.zip
    and return its CRC checksum"""
    print_supported_version_warning(version)
    return safe_get(lambda dd_zip: dd_zip.getinfo(fname(version)).CRC)


def fname(version):
    return "data-dictionary/{version}.xml".format(version=version)


def print_supported_version_warning(version):
    if V(version) < imaspy.OLDEST_SUPPORTED_VERSION:
        logger.warning(
            "Version %s is below lowest supported version of %s.\
            Proceed at your own risk.",
            version,
            imaspy.OLDEST_SUPPORTED_VERSION,
        )


def safe_get(f):
    with ZipFile(ZIPFILE_LOCATION, mode="r") as dd_zip:
        try:
            return f(dd_zip)
        except FileNotFoundError:
            raise FileNotFoundError(
                "IMAS DD zipfile not found at {path}", ZIPFILE_LOCATION
            )
        except KeyError:
            raise FileNotFoundError(
                "IMAS DD version not found in data-dictionary/IDSDef.zip"
            )


def dd_xml_versions():
    """Parse data-dictionary/IDSDef.zip to find version numbers available"""
    dd_prefix_len = len("data-dictionary/")
    return safe_get(
        lambda dd_zip: sorted([f[dd_prefix_len:-4] for f in dd_zip.namelist()], key=V)
    )


def latest_dd_version():
    """Find the latest version in data-dictionary/IDSDef.zip"""
    return dd_xml_versions()[-1]
