# Helper functions to create MDSPlus reference models
# and store them in a cache directory (.cache/imaspy/MDSPlus/name-HASH/)

import logging
import os
import re
import time
from pathlib import Path
from subprocess import CalledProcessError, check_output
from zlib import crc32

from imaspy.dd_helpers import get_saxon
from imaspy.dd_zip import get_dd_xml, get_dd_xml_crc

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


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
    cache_dir_path = Path(_get_xdg_cache_dir()) / "imaspy" / "mdsplus" / cache_dir_name

    try:
        os.makedirs(cache_dir_path, exist_ok=rebuild)
    except FileExistsError:
        if not model_exists(cache_dir_path):
            logger.warning(
                "Model dir %s exists but is empty. Waiting 60s for contents.",
                cache_dir_path,
            )
            for _ in range(120):
                if model_exists(cache_dir_path):
                    break
                time.sleep(1)
            else:
                raise TimeoutError("Timeout exceeded while waiting for MDSplus model")
        else:
            logger.info("Using cached MDSPlus model at %s", cache_dir_path)

        return str(cache_dir_path)

    logger.info(
        "Creating and caching MDSPlus model at %s, this may take a while",
        cache_dir_path,
    )

    create_model_ids_xml(cache_dir_path, fname, version)

    create_mdsplus_model(cache_dir_path)

    return str(cache_dir_path)


def model_exists(path):
    """Given a path to an IDS model definition check if all components are there"""
    return all(
        map(
            lambda f: os.path.isfile(path / f),
            [
                "ids.xml",
                "ids_model.characteristics",
                "ids_model.datafile",
                "ids_model.tree",
                "done.txt",
            ],
        )
    )


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
                + str(
                    Path(__file__).parent / "assets/IDSDef2MDSpreTree.xsl"
                ),  # we have to be careful to have the same version of this file as in the access layer
            ],
            input=get_dd_xml(version) if version else None,
            env={"CLASSPATH": get_saxon(), "PATH": os.environ["PATH"]},
        )
    except CalledProcessError as e:
        if fname:
            logger.error("Error making MDSPlus model IDS.xml for %s", fname)
        else:
            logger.error("Error making MDSplus model IDS.xml for %s", version)
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
            cwd=str(cache_dir_path),
            env={
                "PATH": os.environ["PATH"],
                "LD_LIBRARY_PATH": os.environ["LD_LIBRARY_PATH"],
                "ids_path": str(cache_dir_path),
            },
        )
        # Touch a file to show that we have finished the model
        (cache_dir_path / "done.txt").touch()
    except CalledProcessError as e:
        logger.error("Error making MDSPlus model in {path}", cache_dir_path)
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
    else:
        logger.error("jTraverser.jar not found, cannot build MDSPlus models.")


def ensure_data_dir(user, tokamak, version):
    """Ensure that a data dir exists with a similar algorithm that
    the MDSplus backend uses to set the data path.
    See also mdsplus_backend.cpp:751 (setDataEnv)"""
    if user == "public":
        dir = Path(os.environ["IMAS_HOME"]) / "shared" / "imasdb" / tokamak / version
    elif user[0] == "/":
        dir = Path(user) / tokamak / version
    else:
        dir = Path.home() / "public" / "imasdb" / tokamak / version

    for index in range(10):
        # this is a bit brute force. We could also calculate the index from
        # the run number. But it's only 10 directories...
        (dir / str(index)).mkdir(parents=True, exist_ok=True)
