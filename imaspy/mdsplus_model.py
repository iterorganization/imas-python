# Helper functions to create MDSPlus reference models
# and store them in a cache directory (.cache/imaspy/MDSPlus/name-HASH/)

import logging
import os
import re
import time
from pathlib import Path
from subprocess import CalledProcessError, check_output
from zlib import crc32
import tempfile
import uuid
import shutil
import getpass
import errno

from imaspy.dd_helpers import get_saxon
from imaspy.dd_zip import get_dd_xml, get_dd_xml_crc

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


MDSPLUS_MODEL_TIMEOUT = int(os.getenv("MDSPLUS_MODEL_TIMEOUT", "120"))


def safe_remove(fldr):
    """ Quickly remove a folder on the same filesystem"""
    copy_id = uuid.uuid4()
    tmp_dst = "%s.%s.tmp" % (fldr, copy_id)
    os.rename(fldr, tmp_dst)
    shutil.rmtree(tmp_dst)

def safe_move(src, dst):
    """Rename a folder from ``src`` to ``dst``.

    *   Moves must be atomic.  ``shutil.move()`` is not atomic.
        Note that multiple threads may try to write to the cache at once,
        so atomicity is required to ensure the serving on one thread doesn't
        pick up a partially saved image from another thread.

    *   Moves must work across filesystems.  Often temp directories and the
        cache directories live on different filesystems.  ``os.rename()`` can
        throw errors if run across filesystems.

    So we try ``os.rename()``, but if we detect a cross-filesystem copy, we
    switch to ``shutil.move()`` with some wrappers to make it atomic.
    """
    # From https://alexwlchan.net/2019/03/atomic-cross-filesystem-moves-in-python/
    try:
        os.rename(src, dst)
    except OSError as err:

        if err.errno == errno.EXDEV:
            # Generate a unique ID, and copy `<src>` to the target directory
            # with a temporary name `<dst>.<ID>.tmp`.  Because we're copying
            # across a filesystem boundary, this initial copy may not be
            # atomic.  We intersperse a random UUID so if different processes
            # are copying into `<dst>`, they don't overlap in their tmp copies.
            copy_id = uuid.uuid4()
            tmp_dst = "%s.%s.tmp" % (dst, copy_id)
            shutil.copytree(src, tmp_dst)

            # Then do an atomic rename onto the new name, and clean up the
            # source image.
            try:
                os.rename(tmp_dst, dst)
            except OSError as err:
                if err.errno == errno.EEXIST:
                    # As we use the hash of the files in our foldernames, if the
                    # folder already exists, we can safely assume another
                    # process has put it there before we could, and we should
                    # just remove our tmpdir
                    shutil.rmtree(tmp_dst)
            shutil.rmtree(src)
        elif err.errno == errno.EEXIST:
            shutil.rmtree(src)
        else:
            raise


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

    Args:
        version: DD version string where the cache should be based on

    Kwargs:
        xml_file: Path to the XML to build the cache on
        rebuild: Rebuild the DD cache, overwriting existing cache files

    Returns:
        The path to the requested DD cache
    """

    if version and xml_file:
        raise ValueError("Version OR filename need to be provided, both given")

    # Calculate a checksum on the contents of a DD XML file to uniquely
    # identify our cache files, and re-create them as-needed if the contents
    # of the file change
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

    # There are multiple possible cases for the IMASPy cache
    # 1. The cache exist and can be used
    # 2. The cache exist and needs to be overwritten
    # 3. The cache partially exists, and it is still written by another process, especially during testing
    # 4. The cache partially exists, and is horribly broken
    # 5. The cache does not exist and this process should make it
    #
    # As (cross)-filesystem operations can in principle collide, we use
    # a statistically unique temp dir which we move with a special safe and
    # atomic function if the generation successfully finished

    fuuid = uuid.uuid4().hex
    tmp_cache_dir_path = (
        Path(tempfile.gettempdir())
        / getpass.getuser()
        / "imaspy"
        / "mdsplus"
        / f"{cache_dir_name}_{fuuid}"
    )
    if rebuild:
        # The user has requested a rebuild
        generate_tmp_cache = True
    elif (cache_dir_path.is_dir() and model_exists(cache_dir_path)):
        # The model already exists on the right location, done!
        generate_tmp_cache = False
    elif (cache_dir_path.is_dir() and not model_exists(cache_dir_path)):
        # The cache dir has been created, but not filled.
        # We wait until it fills on its own
        logger.warning(
            "Model dir %s exists but is empty. Waiting %ss for contents.",
            cache_dir_path,
            MDSPLUS_MODEL_TIMEOUT,
        )
        # If it timed out, we will create a new cache in this process
        generate_tmp_cache = final_cache_dir_path = wait_for_model(cache_dir_path)
    elif (not cache_dir_path.is_dir() and not model_exists(cache_dir_path)):
        # The cache did not exist, we will create a new cache in this process
        generate_tmp_cache = True
    else:
        raise RuntimeError("Programmer error, this case should never be true")

    if generate_tmp_cache:
        logger.info(
            "Creating and caching MDSplus model at %s, this may take a while",
            tmp_cache_dir_path,
        )
        cache_dir_path.parent.mkdir(parents=True, exist_ok=True)
        create_model_ids_xml(tmp_cache_dir_path, fname, version)
        create_mdsplus_model(tmp_cache_dir_path)

        logger.info(
            "MDSplus model at %s created, moving to %s ",
            tmp_cache_dir_path,
            cache_dir_path,
        )
        if cache_dir_path.exists():
            safe_remove(cache_dir_path)
        safe_move(tmp_cache_dir_path, cache_dir_path)

    return str(cache_dir_path)

def wait_for_model(cache_dir_path):
    """ Wait MDSPLUS_MODEL_TIMEOUT seconds until model appears in directory

    Returns:
        True if the cache folder is found, and false if the
        wait loop timed out.
    """
    for _ in range(MDSPLUS_MODEL_TIMEOUT):
        if model_exists(cache_dir_path):
            return True
        time.sleep(1)
    else:
        logger.warning(
            "Timeout exceeded while waiting for MDSplus model, try overwriting"
        )
        return False

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
