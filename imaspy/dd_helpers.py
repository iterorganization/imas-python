"""Helper functions to build IDSDef.xml"""

import glob
import logging
import os
import re
import shutil
import subprocess
from packaging.version import Version as V
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZIP_DEFLATED, ZipFile
from typing import Tuple


logger = logging.getLogger("imaspy")
logger.setLevel(logging.INFO)

_idsdef_zip_relpath = Path("imaspy/assets/IDSDef.zip")
_saxon_local_default_name = "saxon9he.jar"  # For pre-3.30.0 builds
_saxon_regex = "saxon(.*).jar"  # Can be used in re.match


def prepare_data_dictionaries():
    """Build IMAS IDSDef.xml files for each tagged version in the DD repository
    1. Search for saxon or download it
    2. Clone the DD repository (ask for user/pass unless ssh key access is available)
    3. Generate IDSDef.xml and rename to IDSDef_${version}.xml
    4. Zip all these IDSDefs together and include in wheel
    """
    import git
    from git import Repo

    saxon_jar_path = get_saxon()
    repo: Repo = get_data_dictionary_repo()
    if repo:
        for tag in repo.tags:
            if V(str(tag)) > V("3.21.1"):
                logger.debug("Building data dictionary version %s", tag)
                build_data_dictionary(repo, tag, saxon_jar_path)

        logger.info("Creating zip file of DD versions")

        if _idsdef_zip_relpath.is_file():
            logger.warning("Overwriting '%s'", _idsdef_zip_relpath)

        with ZipFile(
            _idsdef_zip_relpath,
            mode="w",  # this needs w, since zip can have multiple same entries
            compression=ZIP_DEFLATED,
        ) as dd_zip:
            for filename in glob.glob("data-dictionary/[0-9]*.xml"):
                dd_zip.write(filename)


# pre 3.30.0 versions of the DD have the `saxon9he.jar` file path hardcoded
# in their makefiles. To be sure we can build everything, we link whatever
# saxon we can find to a local file called saxon9he.jar
def get_saxon() -> Path:
    """Search for saxon*.jar and return the path or download it.
    The DD build works by having Saxon in the CLASSPATH, called saxon9he.jar
    until DD version 3.30.0. After 3.30.0 Saxon is found by the SAXONJARFILE env
    variable. We will 'cheat' a little bit later by symlinking saxon9he.jar to
    any version of saxon we found.

    Check:
    1. CLASSPATH
    2. `which saxon`
    3. /usr/share/java/*
    4. or download it
    """

    local_saxon_path = Path.cwd() / _saxon_local_default_name
    if local_saxon_path.exists():
        logger.debug("Something already at '%s' not creating anew", local_saxon_path)
        return local_saxon_path

    saxon_jar_origin = Path(
        find_saxon_classpath()
        or find_saxon_bin()
        or find_saxon_jar()
        or download_saxon()
    )
    logger.info("Found Saxon JAR '%s'", saxon_jar_origin)
    if saxon_jar_origin.name != _saxon_local_default_name:
        try:
            os.symlink(saxon_jar_origin, local_saxon_path)
        except FileExistsError:
            # Another process could have created the symlink while we were searching
            logger.debug(
                "Link '%s' exists, parallel process might've created it",
                local_saxon_path,
            )
        return local_saxon_path
    return saxon_jar_origin


def find_saxon_jar():
    # This finds multiple versions on my system, but they are symlinked together.
    # take the shortest one.
    jars = [
        path
        for path in Path("/usr/share/java").rglob("*")
        if re.match(_saxon_regex, path.name, flags=re.IGNORECASE)
    ]

    if jars:
        saxon_jar_path = min(jars, key=lambda x: len(x.parts))
        return saxon_jar_path


def find_saxon_classpath():
    """Search JAVAs CLASSPATH for a Saxon .jar"""
    classpath = os.environ.get("CLASSPATH", "")
    is_test = lambda x: "test" in x
    is_saxon = lambda x: x.split("/")[-1].startswith("saxon")
    is_jar = lambda x: x.endswith(".jar")
    is_xqj = lambda x: "xqj" in x

    for part in re.split(";|:", classpath):
        if is_jar(part) and is_saxon(part) and not is_test(part) and not is_xqj(part):
            return part


def find_saxon_bin():
    """Search for a saxon executable"""
    saxon_bin = shutil.which("saxon")
    if saxon_bin:
        with open(saxon_bin, "r") as file:
            for line in file:
                saxon_jar_path = re.search("[^ ]*saxon[^ ]*jar", line)
                if saxon_jar_path:
                    return saxon_jar_path.group(0)


def download_saxon():
    """Downloads a zipfile containing Saxon and extract it to the current dir.
    Return the full path to Saxon. This can be any Saxon version. Scripts that
    wrap this should probably manipulate either the name of this file, and/or
    the CLASSPATH"""

    SAXON_PATH = "https://downloads.sourceforge.net/project/saxon/Saxon-HE/10/Java/SaxonHE10-3J.zip"

    resp = urlopen(SAXON_PATH)
    zipfile = ZipFile(BytesIO(resp.read()))
    # Zipfile has a list of the ZipInfos. Look inside for a Saxon jar
    for file in zipfile.filelist:
        if re.match(_saxon_regex, file.filename, flags=re.IGNORECASE):
            path = zipfile.extract(file)
            del zipfile
            return path
    raise FileNotFoundError(f"No Saxon jar found in given zipfile '{SAXON_PATH}'")


def get_data_dictionary_repo() -> Tuple[bool, bool]:
    try:
        import git  # Import git here, the user might not have it!
    except ModuleNotFoundError:
        raise RuntimeError(
            "Could not find 'git' module, try 'pip install gitpython'. \
            Will not build Data Dictionaries!"
        )

        # We need the actual source code (for now) so grab it from ITER
    dd_repo_path = "data-dictionary"

    if "DD_DIRECTORY" in os.environ:
        logger.info("Found DD_DIRECTORY, copying")
        try:
            shutil.copytree(os.environ["DD_DIRECTORY"], dd_repo_path)
        except FileExistsError:
            pass
    else:
        logger.info("Trying to pull data dictionary git repo from ITER")

    # Set up a bare repo and fetch the access-layer repository in it
    os.makedirs(dd_repo_path, exist_ok=True)
    try:
        repo = git.Repo(dd_repo_path)
    except git.exc.InvalidGitRepositoryError:
        repo = git.Repo.init(dd_repo_path)
    logger.info("Set up local git repository {!s}".format(repo))

    try:
        origin = repo.remote()
    except ValueError:
        dd_repo_url = "ssh://git@git.iter.org/imas/data-dictionary.git"
        origin = repo.create_remote("origin", url=dd_repo_url)
    logger.info("Set up remote '{!s}' linking to '{!s}'".format(origin, origin.url))

    try:
        origin.fetch(tags=True)
    except git.exc.GitCommandError as ee:
        logger.warning(
            "Could not fetch tags from %s. Git reports:\n %s." "\nTrying to continue",
            list(origin.urls),
            ee,
        )
    else:
        logger.info("Remote tags fetched")
    return repo


def build_data_dictionary(repo, tag, saxon_jar_path, rebuild=False):
    """Build a single version of the data dictionary given by the tag argument
    if the IDS does not already exist.

    In the data-dictionary repository sometimes IDSDef.xml is stored
    directly, in which case we do not call make.
    """
    if (
        os.path.exists("data-dictionary/{version}.xml".format(version=tag))
        and not rebuild
    ):
        return

    repo.git.checkout(tag, force=True)
    # this could cause issues if someone else has added or left IDSDef.xml
    # in this directory. However, we go through the tags in order
    # so 1.0.0 comes first, where git checks out IDSDef.xml
    if not _idsdef_zip_relpath.exists():
        try:
            subprocess.check_output(
                "make IDSDef.xml 2>/dev/null",
                cwd=os.getcwd() + "/data-dictionary",
                shell=True,
                env={"CLASSPATH": saxon_jar_path, "PATH": os.environ["PATH"]},
            )
        except subprocess.CalledProcessError as ee:
            logger.warning("Error making DD version %s, make reported:", tag)
            print(f"CLASSPATH ='{saxon_jar_path}'")
            print(f"PATH = '{os.environ['PATH']}'")
            print(ee.output.decode("UTF-8"))
    # copy and delete original instead of move (to follow symlink)
    try:
        shutil.copy(
            "data-dictionary/IDSDef.xml",
            "data-dictionary/{version}.xml".format(version=tag),
            follow_symlinks=True,
        )
    except shutil.SameFileError:
        pass
    os.remove("data-dictionary/IDSDef.xml")
