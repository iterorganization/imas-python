# Helper functions to create MDSPlus reference models
# and store them in a cache directory (.cache/imaspy/MDSPlus/name-HASH/)

import logging
import os
from pathlib import Path
from subprocess import CalledProcessError, check_output
from zlib import crc32

from imaspy.dd_helpers import get_saxon
from imaspy.dd_zip import get_dd_xml, get_dd_xml_crc

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.WARNING)


def mdsplus_model_dir(version, xml_file=None, rebuild=False):
    """
    when given a version number this looks for the DD definition
    of that version in the internal cache. Alternatively a filename
    can be passed, which leads us to use that XML file to build an
    MDSplus model directory.


    Given a filename and xml contents create an xml
    document for the mdsplus model by running a command like the below:

    java net.sf.saxon.Transform -s:- -xsl: -o:${OUTPUT_FILE}

    with ENV:
    env={"CLASSPATH": saxon_jar_path, "PATH": os.environ["PATH"]}
    """

    if version and xml_file:
        return ValueError("Version OR filename need to be provided, both given")

    # calculate a ch
    if version:
        crc = get_dd_xml_crc(version)
        xml_name = version + ".xml"
        fname = "-"
        stdin = get_dd_xml(version)
    elif xml_file:
        xml_name = Path(xml_file).filename
        fname = xml_file
        with open(fname, "r") as file:
            crc = crc32(file.read())
        stdin = None
    else:
        return ValueError("Version OR filename need to be provided, none given")

    cache_dir_name = "%s-%08x" % (xml_name, crc)
    cache_dir_path = Path(_get_xdg_cache_dir()) / "imaspy" / "mdsplus" / cache_dir_name

    if not os.path.isdir(cache_dir_path) or rebuild:
        if not os.path.isdir(cache_dir_path):
            os.makedirs(cache_dir_path)

        try:
            check_output(
                [
                    "java",
                    "net.sf.saxon.Transform",
                    "-s:" + fname,
                    "-o:" + str(cache_dir_path / "ids.xml"),
                    "DD_GIT_DESCRIBE=" + (version or fname),
                    "UAL_GIT_DESCRIBE=" + os.environ.get("UAL_VERSION", "0.0.0"),
                    "-xsl:"
                    + str(Path(__file__).parent / "../assets/IDSDef2MDSpreTree.xsl"),
                ],
                input=stdin,
                env={"CLASSPATH": get_saxon(), "PATH": os.environ["PATH"]},
            )
        except CalledProcessError as e:
            if xml_file:
                logger.warning("Error making MDSPlus model for {file}", xml_file)
            else:
                logger.warning("Error making MDSplus model for {version}", version)
            raise e


def _get_xdg_cache_dir():
    """
    Return the XDG cache directory, according to the XDG base directory spec:

    https://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    return os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
