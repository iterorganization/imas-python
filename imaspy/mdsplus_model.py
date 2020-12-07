# Helper functions to create MDSPlus reference models
# and store them in a cache directory (.cache/imaspy/MDSPlus/name-HASH/)

import logging
import os
import re
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
    elif xml_file:
        xml_name = Path(xml_file).name
        fname = xml_file
        with open(fname, "rb") as file:
            crc = crc32(file.read())
    else:
        raise ValueError("Version OR filename need to be provided, none given")

    cache_dir_name = "%s-%08x" % (xml_name, crc)
    cache_dir_path = str(
        Path(_get_xdg_cache_dir()) / "imaspy" / "mdsplus" / cache_dir_name
    )

    if not os.path.isdir(cache_dir_path) or rebuild:
        if not os.path.isdir(cache_dir_path):
            os.makedirs(cache_dir_path)

        logger.info(
            "Creating and caching MDSPlus model at {path}, this may take a while",
            cache_dir_path,
        )

        create_model_ids_xml(cache_dir_path, fname, version)

        create_mdsplus_model(cache_dir_path)
    else:
        logger.info("Using cached MDSPlus model at {path}", cache_dir_path)

    return cache_dir_path


def create_model_ids_xml(cache_dir_path, fname, version):
    """Use saxon to compile an ids.xml suitable for creating an mdsplus model."""

    try:
        check_output(
            [
                "java",
                "net.sf.saxon.Transform",
                "-s:" + str(fname),
                "-o:" + str(Path(cache_dir_path) / "ids.xml"),
                "DD_GIT_DESCRIBE=" + str(version or fname),
                # if this is expected as git describe it might break
                # if we just pass a filename
                "UAL_GIT_DESCRIBE=" + os.environ.get("UAL_VERSION", "0.0.0"),
                "-xsl:"
                + str(Path(__file__).parent / "../assets/IDSDef2MDSpreTree.xsl"),
            ],
            input=get_dd_xml(version) if version else None,
            env={"CLASSPATH": get_saxon(), "PATH": os.environ["PATH"]},
        )
    except CalledProcessError as e:
        if fname:
            logger.warning("Error making MDSPlus model IDS.xml for {file}", fname)
        else:
            logger.warning("Error making MDSplus model IDS.xml for {version}", version)
        raise e


def create_mdsplus_model(cache_dir_path):
    """Use jtraverser to compile a valid MDS model file."""
    try:
        check_output(
            [
                "java",
                "-Xms1g",  # what do these do?
                "-Xmx8g",  # what do these do?
                "-XX:+UseG1GC",  # what do these do?
                "-cp",
                jTraverser_jar(),
                "CompileTree",
                "ids",
            ],
            cwd=cache_dir_path,
            env={"PATH": os.environ["PATH"], "ids_path": cache_dir_path},
        )
    except CalledProcessError as e:
        logger.warning("Error making MDSPlus model in {path}", cache_dir_path)
        raise e


def _get_xdg_cache_dir():
    """
    Return the XDG cache directory, according to the XDG base directory spec:

    https://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    return os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")


def jTraverser_jar():
    """Search a few common locations and CLASSPATH for jTraverser.jar
    which is provided by MDSPlus."""
    search_dirs = ["/usr/share/java"]

    for component in os.environ.get("CLASSPATH", "").split(":"):
        if component.endswith(".jar"):
            if re.search(".*jTraverser.jar", component):
                return component
        else:  # assume its a directory (strip any '*' suffix)
            search_dirs.append(component.rstrip("*"))

    files = []
    for dir in search_dirs:
        files += Path(dir).rglob("*")

    jars = [path for path in files if path.name == "jTraverser.jar"]

    if jars:
        jar_path = min(jars, key=lambda x: len(x.parts))
        return jar_path
