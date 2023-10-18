# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""
Helper module for importing specific functionality from the imas HLI

- Lowlevel bindings (``from imaspy.imas_interface import lowlevel``)
- IMAS constants (``from imaspy.imas_interface import imasdef``)

The whole imas module is also available as a lazy-loaded module:

>>> from imaspy.imas_interface import imas
>>> # The actual imas module is not imported yet
>>> # Once you access attributes the import will take place:
>>> imas.core_profiles
<class 'imas.core_profiles.core_profiles'>

"""
import fnmatch
import importlib.machinery
import importlib.util
import logging
import os.path
import sys
import sysconfig

logger = logging.getLogger(__name__)


# TODO for AL5:
# - imasdef needs extension module imas.al_defs
# - _ual_lowlevel is renamed to _al_lowlevel


def _lazy_import(name):
    if name in sys.modules:
        return sys.modules[name]
    # https://docs.python.org/3/library/importlib.html#implementing-lazy-imports
    spec = importlib.util.find_spec(name)
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def _import_extension_submodule(package_spec, submodule):
    return _import_submodule(
        package_spec, submodule, importlib.machinery.EXTENSION_SUFFIXES
    )


def _import_submodule(package_spec, submodule, extensions):
    fullname = f"imas.{submodule}"
    spec = None
    for search_location in package_spec.submodule_search_locations:
        for ext in extensions:
            location = f"{search_location}/{submodule}{ext}"
            if os.path.exists(location):
                spec = importlib.util.spec_from_file_location(fullname, location)
                break
        if spec:
            break
    if not spec:
        msg = "Spec for %s not found from file location, fall back to find_spec."
        logger.debug(msg, fullname)
        spec = importlib.util.find_spec(fullname)

    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    return module


_imas_spec = importlib.util.find_spec("imas")
if _imas_spec and _imas_spec.submodule_search_locations is None:
    # We found the IMAS loader, do some magic to find the "real" imas package
    pyver = ".".join(str(i) for i in sys.version_info[:2])

    path = os.path.join(
        os.getenv("IMAS_PREFIX"), "python", "lib." + sysconfig.get_platform() + "-" + pyver
    )
    if not os.path.isdir(path):
        path = os.path.join(
            os.getenv("IMAS_PREFIX"),
            "python",
            "lib." + sysconfig.get_platform() + "-cpython-" + pyver.replace(".", ""),
        )

    if os.path.isdir(path):
        # Find the module file name
        names = os.listdir(path)
        namepattern = "imas_" + os.getenv("IMAS_VERSION").replace(".", "_") + "_ual_*"
        namecatchall = "imas_*_ual_*"
        # A python module matching the name pattern with env's IMAS_VERSION is preferred,
        # but may not be found when IMAS_VERSION does not match a proper tag name (e.g.
        # in case of custom branch installation). Then learn the derived version string
        # from the catchall, if it finds exactly 1 in this path.
        name = fnmatch.filter(names, namepattern)
        if len(name) != 1:
            name = fnmatch.filter(names, namecatchall)
        if len(name) == 1:
            # Found a single match, use this name
            name = name[0]
            sys.path.append(path)
            _imas_spec = importlib.util.find_spec(name)

if _imas_spec is None:
    has_imas = False
    imasdef = None
    lowlevel = None
    imas = None
    logger.critical(
        "Module 'imas' could not be imported. Some functionality is not available."
    )

elif _imas_spec and _imas_spec.submodule_search_locations is None:
    # Give up and just import the actual package...
    has_imas = True
    imas = importlib.import_module("imas")
    lowlevel = importlib.import_module("imas._ual_lowlevel")
    imasdef = importlib.import_module("imas.imasdef")

else:
    has_imas = True

    # Required by _ual_lowlevel, will import all of imas if we don't import these first
    imasdef = _import_submodule(_imas_spec, "imasdef", [".py"])
    hli_exception = _import_submodule(_imas_spec, "hli_exception", [".py"])

    # Hack to make the "from hli_exception import ..." and "from imasdef import ..." of
    # _ual_lowlevel.pyx work
    _modules = {"imasdef": imasdef, "hli_exception": hli_exception, "imas": object()}
    _old_modules = {mod: sys.modules.get(mod) for mod in _modules}
    sys.modules.update(_modules)
    lowlevel = _import_extension_submodule(_imas_spec, "_ual_lowlevel")
    # Clean up the global modules
    for mod, old_module in _old_modules.items():
        if old_module is not None:
            sys.modules[mod] = old_module
        else:
            del sys.modules[mod]

    imas = _lazy_import("imas")
