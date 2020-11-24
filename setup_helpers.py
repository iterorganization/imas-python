import logging
import os
import shutil
from itertools import chain
from pathlib import Path
import re

logger = logging.getLogger("imaspy")

this_dir = os.path.abspath(
    os.path.dirname(__file__)
)  # We need to know where we are for many things


def prepare_data_dictionaries():
    """Build IMAS IDSDef.xml files for each tagged version in the DD repository
    1. Search for saxon or download it
    2. Clone the DD repository (ask for user/pass unless ssh key access is available)
    3. Generate IDSDef.xml and rename to IDSDef_${version}.xml
    4. Zip all these IDSDefs together and include in wheel
    """
    saxon_jar_path = get_saxon()
    repo, origin = get_data_dictionary_repo()
    if repo:
        for tag in repo.tags:
            logger.debug("Building data dictionary version {tag}", tag)
            build_data_dictionary(repo, origin, tag, saxon_jar_path)

        from zipfile import ZipFile, ZIP_DEFLATED
        import glob

        logger.info("Creating zip file of DD versions")

        with ZipFile(
            "data-dictionary/IDSDef.zip",
            mode="w",  # this needs w, since zip can have multiple same entries
            compression=ZIP_DEFLATED,
        ) as dd_zip:
            for filename in glob.glob("data-dictionary/[0-9]*.xml"):
                dd_zip.write(filename)


def get_saxon():
    """Search for saxon*.jar and return the path or download it.
    The DD build only works by having saxon9he.jar in the CLASSPATH (until 3.30.0).
    We will 'cheat' a little bit later by symlinking saxon9he.jar to any version
    of saxon we found.

    Check:
    1. CLASSPATH
    2. `which saxon`
    3. /usr/share/java/*
    4. or download it
    """

    local_saxon_path = os.getcwd() + "/saxon9he.jar"
    if os.path.exists(local_saxon_path):
        logger.debug("Something already at ./saxon9he.jar, not creating anew")
        return local_saxon_path

    saxon_jar_origin = Path(
        find_saxon_classpath()
        or find_saxon_bin()
        or find_saxon_jar()
        or download_saxon()
    )
    if not saxon_jar_origin.name == "saxon9he.jar":
        os.symlink(saxon_jar_origin, local_saxon_path)
        return local_saxon_path
    return str(saxon_jar_origin)


def find_saxon_jar():
    import subprocess

    # This finds multiple versions on my system, but they are symlinked together.
    # take the shortest one.
    jars = [
        path
        for path in Path("/usr/share/java").rglob("*")
        if re.match("saxon(.*).jar", path.name, flags=re.IGNORECASE)
    ]

    if jars:
        saxon_jar_path = min(jars, key=lambda x: len(x.parts))
        return saxon_jar_path


def find_saxon_classpath():
    if "CLASSPATH" in os.environ:
        saxon_jar_path = re.search("[^:]*saxon[^:]*jar", os.environ["CLASSPATH"])
        if saxon_jar_path:
            return saxon_jar_path.group(0)


def find_saxon_bin():
    saxon_bin = shutil.which("saxon")
    if saxon_bin:
        with open(saxon_bin, "r") as file:
            for line in file:
                saxon_jar_path = re.search("[^ ]*saxon[^ ]*jar", line)
                if saxon_jar_path:
                    return saxon_jar_path.group(0)


def download_saxon():
    """Downloads a zipfile containing saxon9he.jar and extract it to the current dir.
    Return the full path to saxon9he.jar"""
    from io import BytesIO
    from zipfile import ZipFile
    from urllib.request import urlopen

    SAXON_PATH = (
        "https://iweb.dl.sourceforge.net/project/saxon/Saxon-HE/9.9/SaxonHE9-9-1-4J.zip"
    )

    resp = urlopen(SAXON_PATH)
    zipfile = ZipFile(BytesIO(resp.read()))
    path = zipfile.extract("saxon9he.jar")
    del zipfile
    return path


def get_data_dictionary_repo():
    try:
        import git  # Import git here, the user might not have it!
    except ModuleNotFoundError:
        logger.warning(
            "Could not find 'git' module, try 'pip install gitpython'. \
            Will not build Data Dictionaries!"
        )
        return False, False

        # We need the actual source code (for now) so grab it from ITER
    dd_repo_url = "ssh://git@git.iter.org/imas/data-dictionary.git"
    dd_repo_path = "data-dictionary"

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
        origin = repo.create_remote("origin", url=dd_repo_url)
    logger.info("Set up remote '{!s}' linking to '{!s}'".format(origin, origin.url))

    try:
        origin.fetch("--tags")
    except git.exc.GitCommandError:
        logger.warning("Could not fetch tags from %s", list(origin.urls))
    logger.info("Remote tags fetched")
    return repo, origin


def build_data_dictionary(repo, origin, tag, saxon_jar_path, rebuild=False):
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

    import subprocess

    repo.git.checkout(tag)
    # this could cause issues if someone else has added or left IDSDef.xml
    # in this directory. However, we go through the tags in order
    # so 1.0.0 comes first, where git checks out IDSDef.xml
    if not os.path.exists("data-dictionary/IDSDef.xml"):
        try:
            subprocess.check_output(
                "make IDSDef.xml 2>/dev/null",
                cwd=os.getcwd() + "/data-dictionary",
                shell=True,
                env={"CLASSPATH": saxon_jar_path, "PATH": os.environ["PATH"]},
            )
        except subprocess.CalledProcessError:
            logger.warning("Error making DD version {version}", version=tag)
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


def prepare_ual_sources(ual_symver, ual_commit, force=False):
    """Use gitpython to grab AL sources from ITER repository


    Args:
      - ual_symver: The 'symver style' version to be pulled. e.g. 4.8.2
      - ual_commit: The exact commit to be pulled. Should be a hash or equal to
                    the symver
    """
    try:
        import git  # Import git here, the user might not have it!
    except ModuleNotFoundError:
        logger.warning(
            "Could not find 'git' module, try 'pip install gitpython'. Will not build AL!"
        )
        return False

    # This will probably _always_ depend on the UAL version.
    # However, opposed to the original Python HLI, it does not
    # depend on the IMAS DD version, as that is build dynamically in runtime

    # Now we know which UAL target the user wants to install
    # We need the actual source code (for now) so grab it from ITER
    ual_repo_path = "src/ual"
    ual_repo_url = "ssh://git@git.iter.org/imas/access-layer.git"

    logger.info(
        "Trying to pull commit {!r} symver {!r} "
        "from the {!r} repo at {!r}".format(
            ual_commit, ual_symver, ual_repo_path, ual_repo_url
        )
    )

    # Set up a bare repo and fetch the access-layer repository in it
    os.makedirs(ual_repo_path, exist_ok=True)
    try:
        repo = git.Repo(ual_repo_path)
    except git.exc.InvalidGitRepositoryError:
        repo = git.Repo.init(ual_repo_path)
    logger.info("Set up local git repository {!s}".format(repo))

    try:
        origin = repo.remote()
    except ValueError:
        origin = repo.create_remote("origin", url=ual_repo_url)
    logger.info("Set up remote '{!s}' linking to '{!s}'".format(origin, origin.url))

    origin.fetch("--tags")
    logger.info("Remote tags fetched")

    # First check if we have the commit already
    head = None
    for local_head in repo.heads:
        if local_head.name == ual_commit:
            head = local_head
            logger.info(
                "Found existing head in local repo with commit {!s}".format(head.commit)
            )
            break

    if head is None:
        logger.info("Commit '{!s}' not found locally, trying remote".format(ual_commit))
        # If we do not have the commit, fetch master
        # refspec='remotes/origin/' + ual_commit + ':' + ual_commit
        # refspec = ual_commit + ':' + ual_commit
        refspec = "master"
        logger.info("Fetching refspec {!s}".format(refspec))

        fetch_results = origin.fetch(refspec=refspec)
        if len(fetch_results) == 1:
            head = repo.create_head("HEAD", ual_commit, force=True)
        else:
            raise Exception(
                "Could not create head HEAD from commit '{!s}'".format(ual_commit)
            )

    # Check out remote files locally
    head.checkout()
    described_version = repo.git.describe()
    if described_version != ual_symver:
        raise Exception(
            "Local described version {!r} does"
            " not match requested symver {!r}".format(described_version, ual_symver)
        )

    # We should now have the Python HLI files, check
    hli_src = os.path.join(this_dir, ual_repo_path, "pythoninterface/src/imas")
    if not os.path.isdir(hli_src):
        raise Exception(
            "Python interface src dir does not exist. Should have failed earlier"
        )

    # For the build, we need these
    ual_cython_filelist = [
        "_ual_lowlevel.pyx",
        "ual_defs.pxd",
        "ual_lowlevel_interface.pxd",
    ]
    # We need these in runtime, so check them here
    filelist = ["imasdef.py", "hli_utils.py", "hli_exception.py"]

    # Copy these files into the imaspy directory
    # TODO: This is a bit hacky, do this nicer
    imaspy_libs_dir = os.path.join(this_dir, "imas")
    os.makedirs(imaspy_libs_dir, exist_ok=True)
    # if len(os.listdir(imaspy_libs_dir)) != 0:
    # raise Exception('imaspy libs dir not empty, refusing to overwrite')
    # Make _libs dir act as a python module
    open(os.path.join(imaspy_libs_dir, "__init__.py"), "w").close()

    for file in chain(ual_cython_filelist, filelist):
        path = os.path.join(hli_src, file)
        if not os.path.isfile(path):
            raise Exception(
                "Could not find {!s}, should have failed earlier".format(path)
            )
        else:
            target_path = os.path.join(imaspy_libs_dir, file)
            # Patch some imports, they are different from regular Python HLI and imaspy
            # From PEP-8, absolute imports are preferred https://www.python.org/dev/peps/pep-0008/#id23
            if file == "_ual_lowlevel.pyx":
                with open(path, "r") as old, open(target_path, "w") as new:
                    for line in old:
                        if line == "cimport ual_lowlevel_interface as ual\n":
                            new.write(
                                "cimport imas.ual_lowlevel_interface as ual\n"
                            )
                        elif line == "from imasdef import *\n":
                            new.write("from imas.imasdef import *\n")
                        elif line == "from hli_exception import ALException \n":
                            new.write(
                                "from imas.hli_exception import ALException\n"
                            )
                        else:
                            new.write(line)
            else:
                shutil.copyfile(path, os.path.join(imaspy_libs_dir, file))

    return True


### IMAS-style package names (Not use right now)
def get_ext_filename_without_platform_suffix(filename):
    """ Remove specific system filename extension """
    name, ext = os.path.splitext(filename)
    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")

    if ext_suffix == ext:
        return filename

    ext_suffix = ext_suffix.replace(ext, "")
    idx = name.find(ext_suffix)

    if idx == -1:
        return filename
    else:
        return name[:idx] + ext


def no_cythonize(extensions, **_ignore):
    """Do not use cython, to generate .c files for this extention
    From https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html
    """
    for extension in extensions:
        sources = []
        for sfile in extension.sources:
            path, ext = os.path.splitext(sfile)
            if ext in (".pyx", ".py"):
                if extension.language == "c++":
                    ext = ".cpp"
                else:
                    ext = ".c"
                sfile = path + ext
            sources.append(sfile)
        extension.sources[:] = sources
    return extensions
