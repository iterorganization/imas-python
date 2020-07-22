# Set up 'fancy logging' to display messages to the user
import logging
import imaspy
imaspy_logger = logging.getLogger('imaspy')
logger = imaspy_logger
logger.setLevel(logging.INFO)

# Now that logging is set up, import the rest of the needed packages
import os
import shutil
from itertools import chain
this_dir = os.path.abspath(os.path.dirname(__file__)) # We need to know where we are for many things

def prepare_ual_sources(ual_symver, ual_commit, force=False):
    """ Use gitpython to grab AL sources from ITER repository


    Args:
      - ual_symver: The 'symver style' version to be pulled. e.g. 4.8.2
      - ual_commit: The exact commit to be pulled. Should be a hash or equal to
                    the symver
    """
    try:
        import git # Import git here, the user might not have it!
    except ModuleNotFoundError:
        logger.warning("Could not find 'git' module, try 'pip install gitpython'. Will not build AL!")
        return False

    # This will probably _always_ depend on the UAL version.
    # However, opposed to the original Python HLI, it does not
    # depend on the IMAS DD version, as that is build dynamically in runtime

    # Now we know which UAL target the user wants to install
    # We need the actual source code (for now) so grab it from ITER
    ual_repo_path = 'src/ual'
    ual_repo_url = 'ssh://git@git.iter.org/imas/access-layer.git'

    logger.info("Trying to pull commit {!r} symver {!r} "
                "from the {!r} repo at {!r}".format(
                    ual_commit, ual_symver, ual_repo_path, ual_repo_url))

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
        origin = repo.create_remote('origin', url=ual_repo_url)
    logger.info("Set up remote '{!s}' linking to '{!s}'".format(origin, origin.url))

    origin.fetch('--tags')
    logger.info("Remote tags fetched")

    # First check if we have the commit already
    head = None
    for local_head in repo.heads:
        if local_head.name == ual_commit:
            head = local_head
            logger.info("Found existing head in local repo with commit {!s}".format(head.commit))
            break

    if head is None:
        logger.info("Commit '{!s}' not found locally, trying remote".format(ual_commit))
        # If we do not have the commit, fetch master
        #refspec='remotes/origin/' + ual_commit + ':' + ual_commit
        #refspec = ual_commit + ':' + ual_commit
        refspec = 'master'
        logger.info('Fetching refspec {!s}'.format(refspec))

        fetch_results = origin.fetch(refspec=refspec)
        if len(fetch_results) == 1:
            head = repo.create_head('HEAD', ual_commit, force=True)
        else:
            raise Exception("Could not create head HEAD from commit '{!s}'".format(ual_commit))

    # Check out remote files locally
    head.checkout()
    described_version = repo.git.describe()
    if described_version != ual_symver:
        raise Exception("Local described version {!r} does"
                        " not match requested symver {!r}".format(
                            described_version, ual_symver))

    # We should now have the Python HLI files, check
    hli_src = os.path.join(this_dir, ual_repo_path, 'pythoninterface/src/imas')
    if not os.path.isdir(hli_src):
        raise Exception('Python interface src dir does not exist. Should have failed earlier')


    # For the build, we need these
    ual_cython_filelist = ['_ual_lowlevel.pyx', 'ual_defs.pxd', 'ual_lowlevel_interface.pxd']
    # We need these in runtime, so check them here
    filelist = ['imasdef.py', 'hli_utils.py', 'hli_exception.py']

    # Copy these files into the imaspy directory
    # TODO: This is a bit hacky, do this nicer
    imaspy_libs_dir = os.path.join(this_dir, 'imaspy/_libs')
    os.makedirs(imaspy_libs_dir, exist_ok=True)
    #if len(os.listdir(imaspy_libs_dir)) != 0:
        #raise Exception('imaspy libs dir not empty, refusing to overwrite')
    # Make _libs dir act as a python module
    open(os.path.join(imaspy_libs_dir, '__init__.py'), 'w').close()

    for file in chain(ual_cython_filelist, filelist):
        path = os.path.join(hli_src, file)
        if not os.path.isfile(path):
            raise Exception('Could not find {!s}, should have failed earlier'.format(path))
        else:
            target_path = os.path.join(imaspy_libs_dir, file)
            # Patch some imports, they are different from regular Python HLI and imaspy
            # From PEP-8, absolute imports are preferred https://www.python.org/dev/peps/pep-0008/#id23
            if file == '_ual_lowlevel.pyx':
                with open(path, 'r') as old, open(target_path, 'w') as new:
                    for line in old:
                        if line == 'cimport ual_lowlevel_interface as ual\n':
                            new.write('cimport imaspy._libs.ual_lowlevel_interface as ual\n')
                        elif line == 'from imasdef import *\n':
                            new.write('from imaspy._libs.imasdef import *\n')
                        elif line == 'from hli_exception import ALException \n':
                            new.write('from imaspy._libs.hli_exception import ALException\n')
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
    """ Do not use cython, to generate .c files for this extention
    From https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html
    """
    for extension in extensions:
        sources = []
        for sfile in extension.sources:
            path, ext = os.path.splitext(sfile)
            if ext in ('.pyx', '.py'):
                if extension.language == 'c++':
                    ext = '.cpp'
                else:
                    ext = '.c'
                sfile = path + ext
            sources.append(sfile)
        extension.sources[:] = sources
    return extensions
