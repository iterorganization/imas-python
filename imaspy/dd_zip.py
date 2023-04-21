# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Extract DD versions from a zip file.

The zip file contains files as
* `data-dictionary/3.30.0.xml`
* `data-dictionary/3.29.0.xml`

multiple paths are checked. See `ZIPFILE_LOCATIONS`.
First the environment variable IMASPY_DDZIP is checked.
If that exists and points to a file we will attempt to open it.
Then, IDSDef.zip is searched in site-packages, the current folder,
in .config/imaspy/ (`$$XDG_CONFIG_HOME`) and in
the assets/ folder within the IMASPy package.

1. `$$IMASPY_DDZIP`
2. The virtual environment
3. USER_BASE`imaspy/IDSDef.zip`
4. All `site-packages/imaspy/IDSDef.zip`
5. `./IDSDef.zip`
6. `~/.config/imaspy/IDSDef.zip`
7. `__file__/../../imaspy/assets/IDSDef.zip`

All files are checked, i.e. if your .config/imaspy/IDSDef.zip is outdated
the IMASPy-packaged version will be used.

The `assets/IDSDef.zip` provided with the package can be updated
with the `python setup.py build_DD` command, which is also performed on install
if you have access to the ITER data-dictionary git repo.
Reinstalling imaspy thus also will give you access to the latest DD versions.
"""
import logging
import os
import xml.etree.ElementTree as ET
from packaging.version import Version as V
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile
import site
from typing import List
from importlib_resources import files

import imaspy

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


def _get_xdg_config_dir():
    """
    Return the XDG config directory, according to the XDG base directory spec:

    https://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    return os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")


def _build_zipfile_locations() -> List[Path]:
    """Build a list of potential data dictionary locations.
    We start with the path (if any) of the IMASPY_DDZIP env var.
    Then we look for IDSDef.zip in the current folder, in the
    default XDG config dir (~/.config/imaspy/IDSDef.zip) and
    finally in the assets distributed with this package.
    """
    zip_name = "IDSDef.zip"

    zipfile_locations = [
        os.environ.get("IMASPY_DDZIP"),
        Path(".") / zip_name,
        Path(_get_xdg_config_dir()) / "imaspy" / zip_name,
        files(imaspy) / "assets" / zip_name,
    ]
    # Note that depending on the install method the last path may be inside a zip,
    # as described here: https://importlib-resources.readthedocs.io/en/latest/using.html#file-system-or-zip-file
    # in which case this approach will not work. Let's fix this problem when we run in to it
    return zipfile_locations


ZIPFILE_LOCATIONS = _build_zipfile_locations()


# for version conversion we would expect 2 to be sufficient. Give it some extra space.
@lru_cache(maxsize=4)
def dd_etree(version=None, xml_path=None):
    """Get an ElementTree describing a DD by version or path"""
    if xml_path:
        tree = ET.parse(xml_path)
    elif version:
        tree = ET.ElementTree(ET.fromstring(get_dd_xml(version)))
    else:
        raise ValueError("version or xml_path are required")
    return tree


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


def safe_get(fun):
    """Try to open an IDSDef.zip in one of the locations and perform
    an operation on it."""
    for file in ZIPFILE_LOCATIONS:
        if file is not None and os.path.isfile(file):
            with ZipFile(file, mode="r") as dd_zip:
                try:
                    return fun(dd_zip)
                except KeyError:
                    logger.warning("IMAS DD version not found in %s", file)
    raise FileNotFoundError(
        "IMAS DD zipfile IDSDef.zip not found, checked {!s}".format(ZIPFILE_LOCATIONS)
    )


def dd_xml_versions():
    """Parse IDSDef.zip to find version numbers available"""
    dd_prefix_len = len("data-dictionary/")
    versions = set()
    for file in ZIPFILE_LOCATIONS:
        if file is not None and os.path.isfile(file):
            with ZipFile(file, mode="r") as dd_zip:
                for dd in dd_zip.namelist():
                    versions.add(dd[dd_prefix_len:-4])
    if len(versions) == 0:
        raise FileNotFoundError(
            "No DD versions found, checked {!s}".format(ZIPFILE_LOCATIONS)
        )
    return sorted(list(versions), key=V)


def latest_dd_version():
    """Find the latest version in data-dictionary/IDSDef.zip"""
    return dd_xml_versions()[-1]
