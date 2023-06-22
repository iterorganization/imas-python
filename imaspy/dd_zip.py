# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
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
import difflib
import logging
import os
import re
import xml.etree.ElementTree as ET
from contextlib import contextmanager, nullcontext
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterator, List, Tuple, Union
from zipfile import ZipFile

from importlib_resources import as_file, files
from importlib_resources.abc import Traversable
from packaging.version import InvalidVersion
from packaging.version import Version as V

import imaspy

logger = logging.getLogger(__name__)


def _get_xdg_config_dir():
    """
    Return the XDG config directory, according to the XDG base directory spec:

    https://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    return os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")


def _generate_zipfile_locations() -> Iterator[Union[Path, Traversable]]:
    """Build a list of potential data dictionary locations.
    We start with the path (if any) of the IMASPY_DDZIP env var.
    Then we look for IDSDef.zip in the current folder, in the
    default XDG config dir (~/.config/imaspy/IDSDef.zip) and
    finally in the assets distributed with this package.
    """
    zip_name = "IDSDef.zip"

    environ = os.environ.get("IMASPY_DDZIP")
    if environ:
        yield Path(environ).resolve()

    yield Path(zip_name).resolve()
    yield Path(_get_xdg_config_dir()).resolve() / "imaspy" / zip_name
    yield files(imaspy) / "assets" / zip_name


# Note: DD etrees don't consume a lot of memory, so we'll keep max 32 in memory
_DD_CACHE_SIZE = 32
ZIPFILE_LOCATIONS = list(_generate_zipfile_locations())


@lru_cache(_DD_CACHE_SIZE)
def dd_etree(version=None, xml_path=None):
    """Return the DD element tree corresponding to the provided dd_version or xml_file.

    By default (``dd_version`` and ``dd_xml`` are not supplied), this will attempt
    to get the version from the environment (``IMAS_VERSION``) and use the latest
    available version as fallback.

    You can also specify a specific DD version to use (e.g. "3.38.1") or point to a
    specific data-dictionary XML file. These options are exclusive.

    Args:
        version: DD version string, e.g. "3.38.1".
        xml_path: XML file containing data dictionary definition.
    """
    if version and xml_path:
        raise ValueError("version and xml_path cannot be provided both.")
    if not version and not xml_path:
        # Figure out which DD version to use
        if "IMAS_VERSION" in os.environ:
            imas_version = os.environ["IMAS_VERSION"]
            if imas_version in dd_xml_versions():
                # Use bundled DD version when available
                version = imas_version
            elif "IMAS_PREFIX" in os.environ:
                # Try finding the IDSDef.xml in this installation
                imas_prefix = Path(os.environ["IMAS_PREFIX"]).resolve()
                xml_file = imas_prefix / "include" / "IDSDef.xml"
                if xml_file.exists():
                    xml_path = str(xml_file)
            if not version and not xml_path:
                logger.warning(
                    "Unable to load IMAS version %s, falling back to latest version.",
                    imas_version,
                )
    if not version and not xml_path:
        # Use latest available from
        version = latest_dd_version()

    if xml_path:
        logger.info("Parsing data dictionary from file: %s", xml_path)
        tree = ET.parse(xml_path)
    else:
        xml = get_dd_xml(version)
        logger.info("Parsing data dictionary version %s", version)
        tree = ET.ElementTree(ET.fromstring(xml))
    return tree


@contextmanager
def _open_zipfile(path: Union[Path, Traversable]) -> Iterator[ZipFile]:
    """Open a zipfile, given a Path or Traversable."""
    if isinstance(path, Path):
        ctx = nullcontext(path)
    else:
        ctx = as_file(path)
    with ctx as file:
        with ZipFile(file) as zipfile:
            yield zipfile


@lru_cache
def _read_dd_versions() -> Dict[str, Tuple[Union[Path, Traversable], str]]:
    """Traverse all possible DD zip files and return a map of known versions.

    Returns:
        version_map: version -> contextmanager returning (zipfile path, filename)
    """
    versions = {}
    xml_re = re.compile(r"^data-dictionary/([0-9.]+)\.xml$")
    for path in ZIPFILE_LOCATIONS:
        if not path.is_file():
            continue
        with _open_zipfile(path) as zipfile:
            for fname in zipfile.namelist():
                match = xml_re.match(fname)
                if match:
                    version = match.group(1)
                    if version not in versions:
                        versions[version] = (path, fname)
    if not versions:
        raise RuntimeError(
            "Could not find any data dictionary definitions. "
            f"Looked in: {', '.join(ZIPFILE_LOCATIONS)}."
        )
    return versions


@lru_cache
def dd_xml_versions() -> List[str]:
    """Parse IDSDef.zip to find version numbers available"""

    def sort_key(version):
        try:
            return V(version)
        except InvalidVersion:
            # Don't fail when a malformatted version is present in the DD zip
            logger.error(
                f"Could not convert DD XML version {version} to a Version.", exc_info=1
            )
            return V(0)

    return sorted(_read_dd_versions(), key=sort_key)


def get_dd_xml(version):
    """Read XML file for the given data dictionary version."""
    dd_versions = _read_dd_versions()
    if version not in dd_versions:
        suggestions = ""
        close_matches = difflib.get_close_matches(version, dd_versions, n=1)
        if close_matches:
            suggestions = f" Did you mean {close_matches[0]!r}?"
        raise ValueError(
            f"Data dictionary version {version!r} cannot be found.{suggestions} "
            f"Available versions are: {', '.join(reversed(dd_xml_versions()))}."
        )
    path, fname = dd_versions[version]
    with _open_zipfile(path) as zipfile:
        return zipfile.read(fname)


def get_dd_xml_crc(version):
    """Given a version string, return its CRC checksum"""
    # Note, by this time get_dd_xml is already called, so we don't need to check if the
    # version is known
    path, fname = _read_dd_versions()[version]
    with _open_zipfile(path) as zipfile:
        return zipfile.getinfo(fname).CRC


def print_supported_version_warning(version):
    try:
        if V(version) < imaspy.OLDEST_SUPPORTED_VERSION:
            logger.warning(
                "Version %s is below lowest supported version of %s.\
                Proceed at your own risk.",
                version,
                imaspy.OLDEST_SUPPORTED_VERSION,
            )
    except InvalidVersion:
        logging.warning("Ignoring version parsing error.", exc_info=1)


def latest_dd_version():
    """Find the latest version in data-dictionary/IDSDef.zip"""
    return dd_xml_versions()[-1]
