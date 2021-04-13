# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Core IDS classes

Provides the class for an IDS Primitive data type

* :py:class:`IDSRoot`
"""

import importlib
import os

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

# Set up logging immediately
import numpy as np

from imaspy.al_exception import ALException
from imaspy.context_store import context_store
from imaspy.dd_zip import dd_etree, latest_dd_version
from imaspy.ids_toplevel import IDSToplevel
from imaspy.logger import logger
from imaspy.mdsplus_model import ensure_data_dir, mdsplus_model_dir

try:
    from imaspy.ids_defs import (
        ASCII_BACKEND,
        CLOSE_PULSE,
        DOUBLE_DATA,
        IDS_TIME_MODE_HETEROGENEOUS,
        IDS_TIME_MODE_INDEPENDENT,
        IDS_TIME_MODE_UNKNOWN,
        INTEGER_DATA,
        MDSPLUS_BACKEND,
        MEMORY_BACKEND,
        OPEN_PULSE,
        READ_OP,
        UDA_BACKEND,
    )
except:
    logger.critical("IMAS could not be imported. UAL not available!")


class IDSRoot:
    """ Root of IDS tree. Contains all top-level IDSs """

    depth = 0
    path = ""

    def __init__(
        self,
        s=-1,
        r=-1,
        rs=None,
        rr=None,
        version=None,
        xml_path=None,
        backend_version=None,
        backend_xml_path=None,
        _lazy=True,
    ):
        """Initialize a imaspy IDS tree

        Dynamically build the imaspy IDS tree from the given xml path.
        This does not need necessarily need any associated backend,
        but the structure matches MDSPlus pulsefile. E.g. each Root
        is identified by its shot and run, combining into a UID that
        should be unique per database. IDS tree specifications come from the
        IMAS Data Dictionairy (DD) :dd:`repository`.

        ``version`` or ``xml_path`` is used to build the in_memory structure of
        the underlying Integrated Data Structures (IDSs).

        ``backend_version`` or ``backend_xml_path`` is used in the read/write
        action when reading/writing data nodes, similar to ``version`` and
        ``xml_path``. If neither is specified, use the backend_version as found
        in ``$ids/ids_properties/version_put/data_dictionary`` in the on-disk
        data store. This is a toplevel property, so it is possible to have
        different versions per :py:class:`IDSToplevel`.

        Args:
            s: Shot number
            r: Run number
            rs: Reference shot number
            rr: Reference run number
            version: DD version of the contained data. If given, search the
                local store of DDs for the specified version. If not, default
                to the latest version in the local DD store.
            xml_path: Explicit path to the DD ``IDSRoot.xml``. Overwrites the
                DD version given by ``version`` with the given ``IDSRoot``.
            backend_version: Version of the Data Dictionary used in the
                backend to read/write. Similar to ``version``, but for the
                on-disk data instead of the in-memory structure.
            backend_xml_path: Explicit path the the DD of the backend
                ``IDSRoot.xml``. Overwrites ``version`` similar to ``xml_path``.
            _lazy: If ``True``, only load the template of an :py:class:`IDSToplevel`
                in memory if it is needed, e.g. if a node of the IDS is addressed.
                If ``False``, load all IDSs on initialization time.

        Returns:
            An empty datastructure containing all :py:class:`IDSToplevel` s
            as defined by the given ``version``/``xml_path``.
        """

        self.shot = s
        self.run = r

        if rs is not None:
            raise NotImplementedError("Setting of reference shot")
        if rr is not None:
            raise NotImplementedError("Setting of reference run")

        # The following attributes relate to the UAL-LL
        self.treeName = "ids"
        self.connected = False
        self.expIdx = -1

        self._imas_version = None
        self._xml_path = None

        ver = version or latest_dd_version()
        if xml_path:
            logger.info("Generating IDS structures from file %s", xml_path)
            self._xml_path = xml_path
        else:
            logger.info("Generating IDS structures for version %s", ver)
            self._imas_version = ver
        self._tree = dd_etree(version=ver, xml_path=xml_path)

        self._backend_version = backend_version
        self._backend_xml_path = backend_xml_path

        # Parse given xml_path and build imaspy IDS structures
        self._children = []

        for ids in self._tree.getroot():
            my_name = ids.get("name")
            if my_name is None:
                continue
            if my_name == "version":
                if ids.text != self._imas_version and self._imas_version is not None:
                    logger.error(
                        "Version on file label %s does not match expected version %s",
                        ids.text,
                        self._imas_version,
                    )
                else:
                    logger.info("found version %s", ids.text)
                self._imas_version = ids.text
            else:
                if not _lazy:
                    logger.debug("{:42.42s} tree init".format(my_name))
                    setattr(
                        self,
                        my_name,
                        IDSToplevel(
                            self,
                            my_name,
                            ids,
                            backend_version=self._backend_version,
                            backend_xml_path=self._backend_xml_path,
                        ),
                    )
                self._children.append(my_name)

    def __getattr__(self, key):
        """Lazy get ids toplevel attributes"""
        try:
            return super().__getattribute__(key)
        except AttributeError:
            pass

        if key == "_children":
            return []

        if key in self._children:
            ids = self._tree.getroot().find("./*[@name='{name}']".format(name=key))
            if ids:
                logger.debug("{:42.42s} lazy init".format(key))
                setattr(
                    self,
                    key,
                    IDSToplevel(
                        self,
                        key,
                        ids,
                        backend_version=self._backend_version,
                        backend_xml_path=self._backend_xml_path,
                    ),
                )
        return super().__getattribute__(key)

    @property
    def _version(self):
        return self._imas_version

    # self.equilibrium = IDSToplevel('equilibrium')

    # Do not use this now
    # self.ddunits = DataDictionaryUnits()
    # self.hli_utils = HLIUtils()
    # self.amns_data = amns_data.amns_data()
    # self.barometry = barometry.barometry()
    # etc. etc over all lower level IDSs

    def __getitem__(self, key):
        keyname = str(key)
        return self.__getattr__(keyname)

    def __str__(self, depth=0):
        space = ""
        for i in range(depth):
            space = space + "\t"

        ret = space + "class ids\n"
        ret = (
            ret
            + space
            + "Shot=%d, Run=%d, RefShot%d RefRun=%d\n"
            % (self.shot, self.run, self.refShot, self.refRun)
        )
        ret = (
            ret
            + space
            + "treeName=%s, connected=%d, expIdx=%d\n"
            % (self.treeName, self.connected, self.expIdx)
        )
        ret = ret + space + "Attribute amns_data\n" + self.amns_data.__str__(depth + 1)
        ret = ret + space + "Attribute barometry\n" + self.barometry.__str__(depth + 1)
        # etc. etc over all lower level IDSs
        return ret

    def __del__(self):
        return 1

    def setShot(self, inShot):
        self.shot = inShot

    def setRun(self, inRun):
        self.run = inRun

    def setRefShot(self, inRefShot):
        self.refShot = inRefShot

    def setRefNum(self, inRefRun):
        self.refRun = inRefRun

    def setTreeName(self, inTreeName):
        self.treeName = inTreeName

    def getShot(self):
        return self.shot

    def getRun(self):
        return self.run

    def getRefShot(self):
        return self.refShot

    def getRefRun(self):
        return self.refRun

    def getTreeName(self):
        return self.treeName

    def isConnected(self):
        return self.connected

    def get_units(self, ids, field):
        return self.ddunits.get_units(ids, field)

    def get_units_parser(self):
        return self.ddunits

    def open_ual_store(
        self,
        user,
        tokamak,
        version,
        backend_type,
        mode="r",
        silent=False,
        options="",
        ual_version=None,
    ):
        from imaspy.backends.ual import UALDataStore

        if silent:
            options += "-silent"

        if backend_type == MDSPLUS_BACKEND:
            # ensure presence of mdsplus dir and set environment ids_path
            try:
                _backend_version = self._backend_version or self._imas_version
            except AttributeError:
                _backend_version = None
            try:
                _backend_xml_path = self._backend_xml_path or self._xml_path
            except AttributeError:
                _backend_xml_path = None
            # This does not cover the case of reading an idstoplevel
            # and only then finding out which version it is. But,
            # I think that the model dir is not required if there is an existing
            # file.

            if _backend_xml_path:
                os.environ["ids_path"] = mdsplus_model_dir(
                    version=None, xml_file=_backend_xml_path
                )
            elif _backend_version:
                os.environ["ids_path"] = mdsplus_model_dir(_backend_version)
            else:
                # This doesn't actually matter much, since if we are auto-loading
                # the backend version it is an existing file and we don't need
                # the model (I think). If we are not auto-loading then one of
                # the above two conditions should be true.
                logger.warning(
                    "No backend version information available, "
                    "not building MDSPlus model"
                )

            # ensure presence of model dir
            ensure_data_dir(str(user), tokamak, version)

        # TODO: add more
        backend_names = {
            MDSPLUS_BACKEND: "MDSPLUS",
            ASCII_BACKEND: "ASCII",
            MEMORY_BACKEND: "MEMORY",
            UDA_BACKEND: "UDA",
        }
        logger.info(
            "Opening AL backend %s for %s (shot %s, run %s, user %s, ver %s, mode %s)",
            backend_names[backend_type],
            tokamak,
            self.shot,
            self.run,
            str(user),
            version,
            mode,
        )

        store = UALDataStore.open(
            backend_type,
            tokamak,
            self.shot,
            self.run,
            user_name=str(user),
            data_version=version,
            mode=mode,
            options=options,
            ual_version=ual_version,
        )

        # Save the store internally for magic path detection
        self._data_store = store

        # Do we need to set context like dis?
        self.setPulseCtx(store._idx)
        context_store[store._idx] = "/"

        return store

    def create_env(
        self, user, tokamak, version, silent=False, options="", ual_version=None
    ):
        """Creates a new pulse.

        Parameters
        ----------
        user : string
            Owner of the targeted pulse.
        tokamak : string
            Tokamak name for the targeted pulse.
        version : string
            Data-dictionary major version number for the targeted pulse.
        silent : bool, optional
            Request the lowlevel to be silent (does not print error messages).
        options : string, optional
            Pass additional options to lowlevel.
        ual_version: string, optional
            Specify the UAL version to be used. Use format x.x.x
        """
        store = self.open_ual_store(
            user,
            tokamak,
            version,
            MDSPLUS_BACKEND,
            mode="w",  # This is different per env call
            silent=silent,
            options=options,
            ual_version=ual_version,
        )
        return (0, store._idx)

    def create_env_backend(
        self,
        user,
        tokamak,
        version,
        backend_type,
        silent=False,
        options="",
        ual_version=None,
    ):
        """Creates a new pulse for a UAL supported backend

        Parameters
        ----------
        user : string
            Owner of the targeted pulse.
        tokamak : string
            Tokamak name for the targeted pulse.
        version : string
            Data-dictionary major version number for the targeted pulse.
        backend_type: integer
            One of the backend types (e.g.: MDSPLUS_BACKEND, MEMORY_BACKEND).
        silent : bool, optional
            Request the lowlevel to be silent (does not print error messages).
        options : string, optional
            Pass additional options to lowlevel.
        ual_version: string, optional
            Specify the UAL version to be used. Use format x.x.x
        """
        store = self.open_ual_store(
            user,
            tokamak,
            version,
            backend_type,
            mode="w",  # This is different per env call
            silent=silent,
            options=options,
            ual_version=ual_version,
        )
        return (0, store._idx)

    def open_env(
        self,
        user,
        tokamak,
        version,
        silent=False,
        options="",
        ual_version=None,
        backend_type=None,
    ):
        """Opens an existing pulse.

        Parameters
        ----------
        user : string
            Owner of the targeted pulse.
        tokamak : string
            Tokamak name for the targeted pulse.
        version : string
            Data-dictionary major version number for the targeted pulse.
        silent : bool, optional
            Request the lowlevel to be silent (does not print error messages).
        options : string, optional
            Pass additional options to lowlevel.
        ual_version: string, optional
            Specify the UAL version to be used. Use format x.x.x
        """
        store = self.open_ual_store(
            user,
            tokamak,
            version,
            backend_type,
            mode="r",  # This is different per env call
            silent=silent,
            options=options,
            ual_version=ual_version,
        )
        return (0, store._idx)

    def open_env_backend(
        self,
        user,
        tokamak,
        version,
        backend_type,
        silent=False,
        options="",
        ual_version=None,
    ):
        """Opens an existing pulse for UAL supported backend.

        Parameters
        ----------
        user : string
            Owner of the targeted pulse.
        tokamak : string
            Tokamak name for the targeted pulse.
        version : string
            Data-dictionary major version number for the targeted pulse.
        backend_type: integer
            One of the backend types (e.g.: MDSPLUS_BACKEND, MEMORY_BACKEND).
        silent : bool, optional
            Request the lowlevel to be silent (does not print error messages).
        options : string, optional
            Pass additional options to lowlevel.
        ual_version: string, optional
            Specify the UAL version to be used. Use format x.x.x
        """
        store = self.open_ual_store(
            user,
            tokamak,
            version,
            backend_type,
            mode="r",  # This is different per env call
            silent=silent,
            options=options,
            ual_version=ual_version,
        )
        return (0, store._idx)

    def open_public(self, expName, silent=False):
        """Opens a public pulse with the UAL UAD backend. """
        status, idx = self._ull.ual_begin_pulse_action(
            UDA_BACKEND, self.shot, self.run, "", expName, os.environ["IMAS_VERSION"]
        )
        if status != 0:
            return (status, idx)
        opt = ""
        if silent:
            opt = "-silent"
        status = self._ull.ual_open_pulse(idx, OPEN_PULSE, opt)
        if status != 0:
            return (status, idx)
        self.setPulseCtx(idx)
        context_store[idx] = "/"
        return (status, idx)

    def getPulseCtx(self):
        return self.expIdx

    def setPulseCtx(self, ctx):
        # This sets the contexts of the Root. More-or-less a pointer to a specific pulsefile
        self.expIdx = ctx
        self.connected = True
        # Different than before, IDS TopLevels should get the context from their parent directly
        # self.equilibrium.setPulseCtx(ctx)

    def close(self):
        if self.expIdx != -1:
            status = self._ull.ual_close_pulse(self.expIdx, CLOSE_PULSE, "")
            if status != 0:
                return status
            self.connected = False
            self.expIdx = -1
            return status

    def enableMemCache(self):
        return 1

    def disableMemCache(self):
        return 1

    def discardMemCache(self):
        return 1

    def flushMemCache(self):
        return 1

    def getTimes(self, path):
        homogenousTime = IDS_TIME_MODE_UNKNOWN
        if self.expIdx < 0:
            raise ALException("ERROR: backend not opened.")

        # Create READ context
        status, ctx = self._ull.ual_begin_global_action(self.expIdx, path, READ_OP)
        if status != 0:
            raise ALException("Error calling ual_begin_global_action() for ", status)

        # Check homogeneous_time
        status, homogenousTime = self._ull.ual_read_data(
            ctx, "ids_properties/homogeneous_time", "", INTEGER_DATA, 0
        )
        if status != 0:
            raise ALException("ERROR: homogeneous_time cannot be read.", status)

        if homogenousTime == IDS_TIME_MODE_UNKNOWN:
            status = self._ull.ual_end_action(ctx)
            if status != 0:
                raise ALException("Error calling ual_end_action().", status)
            return 0, []
        # Heterogeneous IDS #
        if homogenousTime == IDS_TIME_MODE_HETEROGENEOUS:
            status = self._ull.ual_end_action(ctx)
            if status != 0:
                raise ALException("ERROR calling ual_end_action().", status)
            return 0, [np.NaN]

        # Time independent IDS #
        if homogenousTime == IDS_TIME_MODE_INDEPENDENT:
            status = self._ull.ual_end_action(ctx)
            if status != 0:
                raise ALException("ERROR calling ual_end_action().", status)
            return 0, [np.NINF]

        # Get global time
        timeList = []
        status, data = self._ull.ual_read_data_array(
            ctx, "time", "/time", DOUBLE_DATA, 1
        )
        if status != 0:
            raise ALException("ERROR: Time vector cannot be read.", status)
        if data is not None:
            timeList = data
        status = self._ull.ual_end_action(ctx)
        if status != 0:
            raise ALException("ERROR calling ual_end_action().", status)
        return status, timeList

    @cached_property
    def _ull(self):
        ctx_path = context_store[self.expIdx]
        if ctx_path != "/":
            raise Exception("{!s} context does not seem to be toplevel".format(self))
        ual_file = self._data_store._manager.acquire()
        ull = importlib.import_module(ual_file.ual_module_name)
        return ull

    # copied since IDSMixin is not used by IDSRoot
    def __getstate__(self):
        """Override getstate so _ull is not passed along. Otherwise we have
        problems deepcopying elements"""

        state = self.__dict__.copy()
        try:
            del state["_ull"]
        except KeyError:
            pass
        return state
