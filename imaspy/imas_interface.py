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

from packaging.version import Version

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
        os.getenv("IMAS_PREFIX"),
        "python",
        "lib." + sysconfig.get_platform() + "-" + pyver,
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

    # Now delete all loaded submodules from sys.modules, otherwise below lazy import
    # doesn't work correctly
    for mod in [mod for mod in sys.modules if mod.startswith("imas.")]:
        del sys.modules[mod]

    imas = _lazy_import("imas")


class LowlevelInterface:
    """Compatibility object.

    Provides a stable API for the rest of IMASPy even when the `imas.lowlevel` interface
    changes.

    .. rubric:: Developer notes

    - When initializing the singleton object, we determine the AL version and redefine
      all methods that exist in the imported lowlevel module.
    - If the lowlevel introduces new methods, we need to:

        1.  Add a new method with the same name but prefix dropped (e.g. register_plugin
            for lowlevel.al_register_plugin)
        2.  The implementation of this method should provide a proper error message when
            the method is called and the underlying lowlevel doesn't provide the
            functionality. For instance ``raise self._minimal_version("5.0")``.

    - If the lowlevel drops methods, we need to update the implementation fo the method
      to provide a proper error message or a workaround.
    - Renamed methods (if this will ever happen) are perhaps best handled in the
      __init__ by providing a mapping of new to old name, so far this was only relevant
      for the ``ual_`` to ``al_`` rename.
    """

    def __init__(self, lowlevel):
        self._lowlevel = lowlevel
        self._al_version = None
        self._al_version_str = ""
        public_methods = [attr for attr in dir(self) if not attr.startswith("_")]

        # AL not available
        if self._lowlevel is None:
            # Replace all our public methods by _imas_not_available
            for method in public_methods:
                setattr(self, method, self._imas_not_available)
            return

        # Lowlevel available, try to determine AL version
        if hasattr(lowlevel, "get_al_version"):
            # Introduced after 5.0.0
            self._al_version_str = self._lowlevel.get_al_version()
            self._al_version = Version(self._al_version_str)
        elif hasattr(lowlevel, "al_read_data"):
            # In AL 5.0.0, all `ual_` methods were renamed to `al_`
            self._al_version_str = "5.0.0"
            self._al_version = Version(self._al_version_str)
        else:
            # AL 4, don't try to determine in more detail
            self._al_version_str = "4.?.?"
            self._al_version = Version("4")

        if self._al_version < Version("5"):
            method_prefix = "ual_"
        else:
            method_prefix = "al_"
        # Overwrite all of our methods that are implemented in the lowlevel
        for method in public_methods:
            ll_method = getattr(lowlevel, method_prefix + method, None)
            if ll_method is not None:
                setattr(self, method, ll_method)

    def _imas_not_available(self):
        raise RuntimeError(
            "This function requires an imas installation, which is not available."
        )

    def _minimal_version(self, minversion):
        return RuntimeError(
            f"This function requires at least Access Layer version {minversion}, "
            f"but the current version is {self._al_version_str}"
        )

    # AL 4 lowlevel API

    def begin_pulse_action(self, backendID, shot, run, user, tokamak, version):
        # Removed in AL5, compatibility handled in DBEntry
        raise NotImplementedError(f"{__qualname__} is not implemented")

    def open_pulse(self, pulseCtx, mode, options):
        # Removed in AL5, compatibility handled in DBEntry
        raise NotImplementedError(f"{__qualname__} is not implemented")

    def close_pulse(self, pulseCtx, mode, options):
        raise NotImplementedError(f"{__qualname__} is not implemented")

    def begin_global_action(self, pulseCtx, dataobjectname, rwmode, datapath=""):
        # datapath was added in AL5 to support more efficient partial_get in the
        # UDA backend. TODO: figure out if this is useful for lazy loading.
        raise NotImplementedError(f"{__qualname__} is not implemented")

    def begin_slice_action(self, pulseCtx, dataobjectname, rwmode, time, interpmode):
        raise NotImplementedError(f"{__qualname__} is not implemented")

    def end_action(self, ctx):
        raise NotImplementedError(f"{__qualname__} is not implemented")

    def write_data(self, ctx, pyFieldPath, pyTimebasePath, inputData):
        raise NotImplementedError(f"{__qualname__} is not implemented")

    def read_data(self, ctx, fieldPath, pyTimebasePath, ualDataType, dim):
        raise NotImplementedError(f"{__qualname__} is not implemented")

    def delete_data(self, ctx, path):
        raise NotImplementedError(f"{__qualname__} is not implemented")

    def begin_arraystruct_action(self, ctx, path, pyTimebase, size):
        raise NotImplementedError(f"{__qualname__} is not implemented")

    def iterate_over_arraystruct(self, aosctx, step):
        raise NotImplementedError(f"{__qualname__} is not implemented")

    # New methods added in AL 5.0

    def build_uri_from_legacy_parameters(
        self, backendID, pulse, run, user, tokamak, version, options
    ):
        raise self._minimal_version("5.0")

    def begin_dataentry_action(self, uri, mode):
        raise self._minimal_version("5.0")

    def register_plugin(self, name):
        raise self._minimal_version("5.0")

    def unregister_plugin(self, name):
        raise self._minimal_version("5.0")

    def bind_plugin(self, path, name):
        raise self._minimal_version("5.0")

    def unbind_plugin(self, path, name):
        raise self._minimal_version("5.0")

    def bind_readback_plugins(self, ctx):
        raise self._minimal_version("5.0")

    def unbind_readback_plugins(self, ctx):
        raise self._minimal_version("5.0")

    def write_plugins_metadata(self, ctx):
        raise self._minimal_version("5.0")

    def setvalue_parameter_plugin(self, parameter_name, inputData, pluginName):
        raise self._minimal_version("5.0")

    def get_al_version(self):
        return self._al_version_str


ll_interface = LowlevelInterface(lowlevel)
"""IMASPy <-> IMAS lowlevel interface"""
