# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Core IDS classes

Provides the class for an IDS Primitive data type

* :py:class:`IDSRoot`
"""

import importlib
import os
import xml.etree.ElementTree as ET

# Set up logging immediately
import numpy as np
from imaspy.al_exception import ALException
from imaspy.context_store import context_store
from imaspy.dd_zip import get_dd_xml
from imaspy.ids_defs import (
    CLOSE_PULSE,
    DOUBLE_DATA,
    IDS_TIME_MODE_HETEROGENEOUS,
    IDS_TIME_MODE_INDEPENDENT,
    IDS_TIME_MODE_UNKNOWN,
    INTEGER_DATA,
    MDSPLUS_BACKEND,
    OPEN_PULSE,
    READ_OP,
    UDA_BACKEND,
)
from imaspy.ids_toplevel import IDSToplevel
from imaspy.logger import logger, loglevel


class IDSRoot:
    """ Root of IDS tree. Contains all top-level IDSs """

    depth = 0
    path = ""

    @loglevel
    def __init__(self, s=-1, r=-1, rs=None, rr=None, version=None, xml_path=None):
        """Initialize a imaspy IDS tree

        Dynamically build the imaspy IDS tree from the given xml path.
        This does not need necessarily need any associated backend,
        but the structure matches MDSPlus pulsefile. E.g. each Root
        is identified by its shot and run, combining into a UID that
        should be unique per database.

        if version is specified search the local set of IMAS DD definitions
        for that version. if xml_path is explicitly specified, ignore version.
        """
        setattr(self, "shot", s)
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

        if version:
            XMLtreeIDSDef = ET.ElementTree(ET.fromstring(get_dd_xml(version)))
            logger.info("Generating IDS structures for version %s", version)
            self.version = version
        elif xml_path:
            XMLtreeIDSDef = ET.parse(xml_path)
            logger.info("Generating IDS structures from file %s", xml_path)
            self.xml_path = xml_path
        else:
            raise ValueError("version or xml_path are required")

        # Parse given xml_path and build imaspy IDS structures
        root = XMLtreeIDSDef.getroot()
        self._children = []
        for ids in root:
            my_name = ids.get("name")
            # Only build for equilibrium to KISS
            if my_name is None:
                continue
            logger.debug("{:42.42s} initialization".format(my_name))
            self._children.append(my_name)
            setattr(self, my_name, IDSToplevel(self, my_name, ids))

    # self.equilibrium = IDSToplevel('equilibrium')

    # Do not use this now
    # self.ddunits = DataDictionaryUnits()
    # self.hli_utils = HLIUtils()
    # self.amns_data = amns_data.amns_data()
    # self.barometry = barometry.barometry()
    # etc. etc over all lower level IDSs

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

        store = UALDataStore.open(
            backend_type,
            tokamak,
            self.shot,
            self.run,
            user_name=user,
            data_version=version,
            mode=mode,
            options=options,
            ual_version=ual_version,
        )

        # Safe the store internally for magic path detection
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

    @property
    def _ull(self):
        ctx_path = context_store[self.expIdx]
        if ctx_path != "/":
            raise Exception("{!s} context does not seem to be toplevel".format(self))
        ual_file = self._data_store._manager.acquire()
        ull = importlib.import_module(ual_file.ual_module_name)
        return ull
