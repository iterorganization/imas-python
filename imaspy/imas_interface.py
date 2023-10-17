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
import importlib.machinery
import importlib.util
import logging
import os.path
import sys

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


def _import_extension_submodule(package, submodule):
    return _import_submodule(package, submodule, importlib.machinery.EXTENSION_SUFFIXES)


def _import_submodule(package, submodule, extensions):
    fullname = f"{package}.{submodule}"
    package_spec = importlib.util.find_spec(package)
    spec = None
    for search_location in package_spec.submodule_search_locations:
        for ext in extensions:
            location = f"{search_location}/{submodule}{ext}"
            if os.path.exists(location):
                spec = importlib.util.spec_from_file_location(submodule, location)
                break
        if spec:
            break
    if not spec:
        msg = "Spec for %s not found from file location, fall back to find_spec."
        breakpoint()
        logger.debug(msg, fullname)
        spec = importlib.util.find_spec(fullname)

    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    return module


_imas_spec = importlib.util.find_spec("imas")
if _imas_spec is None:
    has_imas = False
    imasdef = None
    lowlevel = None
    imas = None
    logger.critical(
        "Module 'imas' could not be imported. Some functionality is not available."
    )
else:
    has_imas = True

    # Required by _ual_lowlevel, will import all of imas if we don't import these first
    imasdef = _import_submodule("imas", "imasdef", [".py"])
    hli_exception = _import_submodule("imas", "hli_exception", [".py"])

    # Hack to make the "from hli_exception import ..." and "from imasdef import ..." of
    # _ual_lowlevel.pyx work
    _modules = {"imasdef": imasdef, "hli_exception": hli_exception}
    _old_modules = {mod: sys.modules.get(mod) for mod in _modules}
    sys.modules.update(_modules)
    lowlevel = _import_extension_submodule("imas", "_ual_lowlevel")
    # Clean up the global modules
    for mod, old_module in _old_modules.items():
        if old_module is not None:
            sys.modules[mod] = old_module
        else:
            del sys.modules[mod]

    imas = _lazy_import("imas")
