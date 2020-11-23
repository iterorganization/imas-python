# This file is part of IMASPy.
#
# IMASPy is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IMASPy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with IMASPy.  If not, see <https://www.gnu.org/licenses/>.
# Set up logging immediately
import copy
import functools
import importlib
import logging
import numbers
import os
import xml.etree.ElementTree as ET

import numpy as np

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.WARNING)


try:
    import imas.hli_utils as hli_utils
    from imas.imasdef import (
        MDSPLUS_BACKEND,
        OPEN_PULSE,
        READ_OP,
        EMPTY_INT,
        FORCE_CREATE_PULSE,
        IDS_TIME_MODE_UNKNOWN,
        IDS_TIME_MODES,
        IDS_TIME_MODE_HOMOGENEOUS,
        IDS_TIME_MODE_HETEROGENEOUS,
        WRITE_OP,
        CHAR_DATA,
        INTEGER_DATA,
        EMPTY_FLOAT,
        DOUBLE_DATA,
        NODE_TYPE_STRUCTURE,
        CLOSE_PULSE,
    )
except ImportError:
    logger.critical("IMASPy _libs could not be imported. UAL not available!")
else:
    # Translation dictionary to go from an ids (primitive) type (without the dimensionality) to a default value
    ids_type_to_default = {
        "STR": "",
        "INT": EMPTY_INT,
        "FLT": EMPTY_FLOAT,
    }


class ContextStore(dict):
    """Stores global UAL context

    A context is a sort of pointer but to where depends on the type of context:
      - PulseContext: identifies a specific entry in database
      - OperationContext: identifies a specific I/O operation (read/write,
        global/slice, which IDS, etc...) being performed on a specific
        PulseContext
      - ArraystructContext: identifies a array of structure node within the IDS
        for a specific operation

    The rest of the absolute path (from last context to leaf/data) is not stored
    in context but passed directly to ual_read and ual_write LL functions.
    Contexts have a fullPath() method that will return string with pseudo
    fullpath up to this context
    """

    def __setitem__(self, key, value):
        """Store context id (key) and full path (value)

        As context is stored globally within the LL-UAL beyond our reach,
        do not allow for duplicated contexts to be opened.
        """
        if key in self:
            raise Exception(
                "Trying to set context {!s} to {!s}, but was not released. Currently is {!s}".format(
                    key, value, self[key]
                )
            )
        else:
            super().__setitem__(key, value)

    def update(self, ctx, newCtx):
        if ctx not in self:
            raise Exception("Trying to update non-existing context {!s}".format(ctx))
        super().__setitem__(ctx, newCtx)

    def decodeContextInfo(self, ctxLst=None):
        """Decode ual context info to Python-friendly format"""
        if ctxLst is None:
            ctxLst = self.keys()
        elif ctxLst is not None and not isinstance(cnxLst, list):
            ctxLst = list(ctxLst)
        if any(not np.issubdtype(type(ctx), np.integer) for ctx in ctxLst):
            raise ValuError("ctx identifier should be an integer")
        for ctx in ctxLst:
            # This seems to cause memory corruption
            # Sometimes..
            contextInfo = self._ull.ual_context_info(ctx)
            infoCopy = (contextInfo + ".")[:-1]
            info = {}
            for line in infoCopy.split("\n"):
                if line == "":
                    continue
                key, val = line.split("=")
                info[key.strip()] = val.strip()
            print("ctx", ctx, info)


# Keep the context store on the module level
# TODO: Decide if this is the place to put it. How 'global' is 'global'?
context_store = ContextStore()


class ALException(Exception):
    def __init__(self, message, errorStatus=None):
        if errorStatus is not None:
            Exception.__init__(self, message + "\nError status=" + str(errorStatus))
        else:
            Exception.__init__(self, message)


def loglevel(func):
    """Generate a decorator for setting the logger level on a function"""

    @functools.wraps(func)
    def loglevel_decorator(*args, **kwargs):
        verbosity = kwargs.pop("verbosity", None)
        if verbosity is not None:
            old_log_level = logger.level
            if verbosity >= 1:
                logger.setLevel(logging.INFO)
            if verbosity >= 2:
                logger.setLevel(logging.DEBUG)
        value = func(*args, **kwargs)
        if verbosity is not None:
            logger.setLevel(old_log_level)
        return value

    return loglevel_decorator


class IDSMixin:
    @loglevel
    def getRelCTXPath(self, ctx):
        """ Get the path relative to given context from an absolute path"""
        # This could be replaced with the fullPath() method provided by the LL-UAL
        if self.path.startswith(context_store[ctx]):
            # If the given path indeed starts with the context path. This should
            # always be the case. Grab the part of the path _after_ the context
            # path string
            if context_store[ctx] == "/":
                # The root context is special, it does not have a slash before
                rel_path = self.path[len(context_store[ctx]) :]
            else:
                rel_path = self.path[len(context_store[ctx]) + 1 :]
            split = rel_path.split("/")
            try:
                # Check if the first part of the path is a number. If it is,
                # strip it, it is implied by context
                int(split[0])
            except (ValueError):
                pass
            else:
                # Starts with numeric, strip. Is captured in context
                # TODO: Might need to be recursive.
                rel_path = "/".join(split[1:])
        else:
            raise Exception("Could not strip context from absolute path")
        # logger.debug('Got context {!s} with abspath {!s}, relpath is {!s}'.format(ctx, self.path, rel_path))
        return rel_path

    def getTimeBasePath(self, homogeneousTime, ignore_nbc_change=1):
        strTimeBasePath = ""
        # Grab timebasepath from the coordinates.
        # TODO: In some cases the timebasepath is stored in the XML directly.
        #       What has priority in case it conflicts? Regardless, this is not
        #       handled by imaspy atm
        if self._coordinates != {}:
            if (
                self._coordinates["coordinate1"].endswith("time")
                and "coordinate2" not in self._coordinates
            ):
                # Should Walk up the tree
                # Just stupid copy for now
                # strTimeBasePath = self._coordinates['coordinate1']
                if homogeneousTime == IDS_TIME_MODE_HOMOGENEOUS:
                    strTimeBasePath = "/time"
                elif homogeneousTime == IDS_TIME_MODE_HETEROGENEOUS:
                    strTimeBasePath = self.getAOSPath(ignore_nbc_change) + "/time"
                else:
                    raise ALException(
                        "Unexpected call to function getTimeBasePath(cls, homogeneousTime) with undefined homogeneous time."
                    )
                pass
            elif (
                self._coordinates["coordinate1"] == "1...N"
                and "coordinate2" not in self._coordinates
            ):
                # If variable only depends on 1...N, no timebasepath
                pass
            else:
                # Stub for explicit handling of other cases
                pass

        return strTimeBasePath

    def getAOSPath(self, ignore_nbc_change=1):
        # TODO: Fix in case it gives trouble
        # This is probably wrong! Should walk up the tree
        return self._name

    @property
    def path(self):
        """Build absolute path from node to root"""
        # Probably superseded by the property below
        my_path = self._name
        if hasattr(self, "_parent"):
            my_path = self._parent.path + "/" + my_path
        return my_path

    @property
    def path(self):
        """Build absolute path from node to root"""
        my_path = self._name
        if hasattr(self, "_parent"):
            if isinstance(self._parent, IDSStructArray):
                my_path = "{!s}/{!s}".format(
                    self._parent.path, self._parent.value.index(self)
                )
            else:
                my_path = self._parent.path + "/" + my_path
        return my_path

    @property
    def _ull(self):
        if not hasattr(self, "_parent"):
            raise Exception("ULL directly connected to {!s}".format(self))
        return self._parent._ull


class IDSPrimitive(IDSMixin):
    """IDS leaf node

    Represents actual data. Examples are (arrays of) strings, floats, integers.
    Lives entirely in-memory until 'put' into a database.
    """

    @loglevel
    def __init__(
        self, name, ids_type, ndims, parent=None, value=None, coordinates=None
    ):
        """Initialize IDSPrimitive

        args:
          - name: Name of the leaf node. Will be used in path generation when
                  stored in DB
          - ids_type: String representing the IDS type. Will be used to convert
                      to Python equivalent
          - ndims: Dimensionality of data

        kwargs:
          - parent: Parent node of this leaf. Can be anything with a _path attribute.
                    Will be used in path generation when stored in DB
          - value: Value to fill the leaf with. Can be anything castable by
                   IDSPrimitive.cast_value. If not given, will be filled by
                   default data matching given ids_type and ndims
          - coordinates: Data coordinates of the node
        """
        if ids_type != "STR" and ndims != 0 and self.__class__ == IDSPrimitive:
            raise Exception(
                "{!s} should be 0D! Got ndims={:d}. Instantiate using IDSNumericArray instead".format(
                    self.__class__, ndims
                )
            )
        if ndims == 0:
            self._default = ids_type_to_default[ids_type]
        else:
            self._default = np.full((1,) * ndims, ids_type_to_default[ids_type])
        if value is None:
            value = self._default
        self._ids_type = ids_type
        self._ndims = ndims
        self._name = name
        self._parent = parent
        self._coordinates = coordinates
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, setter_value):
        if isinstance(setter_value, type(self)):
            # No need to cast, just overwrite contained value
            if (
                setter_value._ids_type == self._ids_type
                and setter_value._ndims == self._ndims
            ):
                self.__value = setter_value.value
            # Can we cast the internal value to a valid value?
            else:
                self.__value = self.cast_value(setter_value.value)
        else:
            self.__value = self.cast_value(setter_value)

    def cast_value(self, value):
        # Cast list-likes to arrays
        if isinstance(value, (list, tuple)):
            value = np.array(value)

        # Cast values to their IDS-python types
        if self._ids_type == "STR" and self._ndims == 0:
            value = str(value)
        elif self._ids_type == "INT" and self._ndims == 0:
            value = int(value)
        elif self._ids_type == "FLT" and self._ndims == 0:
            value = float(value)
        elif self._ndims >= 1:
            if self._ids_type == "FLT":
                value = np.array(value, dtype=np.float64)
            elif self._ids_type == "INT":
                value = np.array(value, dtype=np.int64)
            else:
                logger.critical(
                    "Unknown numpy type {!s}, cannot convert from python to IDS type".format(
                        value.dtype
                    )
                )
                embed()
                raise Exception
        else:
            logger.critical(
                "Unknown python type {!s}, cannot convert from python to IDS type".format(
                    type(value)
                )
            )
            embed()
            raise Exception
        return value

    @loglevel
    def put(self, ctx, homogeneousTime):
        """Put data into UAL backend storage format

        Does minor sanity checking before calling the cython backend.
        Tries to dynamically build all needed information for the UAL.
        """
        if self._name is None:
            raise Exception("Location in tree undefined, cannot put in database")
        # Convert imaspy ids_type to ual scalar_type
        if self._ids_type == "INT":
            scalar_type = 1
        elif self._ids_type == "FLT":
            scalar_type = 2
        elif self._ids_type == "CPX":
            scalar_type = 3

        # Check sanity of given data
        if self._ids_type in ["INT", "FLT", "CPX"] and self._ndims == 0:
            data = hli_utils.HLIUtils.isScalarFinite(self.value, scalar_type)
        elif self._ids_type in ["INT", "FLT", "CPX"]:
            if not hli_utils.HLIUtils.isTypeValid(self.value, self._name, "NP_ARRAY"):
                raise Exception
            data = hli_utils.HLIUtils.isFinite(self.value, scalar_type)
        else:
            data = self.value

        # Do not write if data is the same as the default of the leaf node
        if np.all(data == self._default):
            return

        dbg_str = " " + " " * self.depth + "- " + self._name
        dbg_str += (" {:" + str(max(0, 53 - len(dbg_str))) + "s}").format(
            "(" + str(data) + ")"
        )
        # Call signature
        # ual_write_data(ctx, pyFieldPath, pyTimebasePath, inputData, dataType=0, dim = 0, sizeArray = np.empty([0], dtype=np.int32))
        data_type = self._ull._getDataType(data)

        # Strip context from absolute path
        rel_path = self.getRelCTXPath(ctx)
        # TODO: Check ignore_nbc_change
        strTimeBasePath = self.getTimeBasePath(homogeneousTime)

        logger.info("{:54.54s} write".format(dbg_str))
        logger.debug(
            "   {:50.50s} write".format("/".join([context_store[ctx], rel_path]))
        )
        status = self._ull.ual_write_data(
            ctx, rel_path, strTimeBasePath, data, dataType=data_type, dim=self._ndims
        )
        if status != 0:
            raise ALException('Error writing field "{!s}"'.format(self._name))

    @loglevel
    def get(self, ctx, homogeneousTime):
        """Get data from UAL backend storage format

        Tries to dynamically build all needed information for the UAL.
        Does currently _not_ set value of the leaf node, this is handled
        by the IDSStructure.
        """
        # Strip context from absolute path
        strNodePath = self.getRelCTXPath(ctx)
        strTimeBasePath = self.getTimeBasePath(homogeneousTime)
        if self._ids_type == "STR" and self._ndims == 0:
            status, data = self._ull.ual_read_data_string(
                ctx, strNodePath, strTimeBasePath, CHAR_DATA, 1
            )
        elif self._ids_type == "INT" and self._ndims == 0:
            status, data = self._ull.ual_read_data_scalar(
                ctx, strNodePath, strTimeBasePath, INTEGER_DATA
            )
        elif self._ids_type == "FLT" and self._ndims == 0:
            status, data = self._ull.ual_read_data_scalar(
                ctx, strNodePath, strTimeBasePath, DOUBLE_DATA
            )
        elif self._ids_type == "FLT" and self._ndims > 0:
            status, data = self._ull.ual_read_data_array(
                ctx, strNodePath, strTimeBasePath, DOUBLE_DATA, self._ndims
            )
        elif self._ids_type == "INT" and self._ndims > 0:
            status, data = self._ull.ual_read_data_array(
                ctx, strNodePath, strTimeBasePath, INTEGER_DATA, self._ndims
            )
        else:
            logger.critical(
                "Unknown type {!s} ndims {!s} of field {!s}, skipping for now".format(
                    self._ids_type, self._ndims, self._name
                )
            )
            status = data = None
        return status, data

    @property
    def depth(self):
        """Calculate the depth of the leaf node"""
        my_depth = 0
        if hasattr(self, "_parent"):
            my_depth += self._parent.depth
        return my_depth

    def __repr__(self):
        return '%s("%s", %r)' % (type(self).__name__, self._name, self.value)

    @property
    def data_type(self):
        """Combine imaspy ids_type and ndims to UAL data_type"""
        return "{!s}_{!s}D".format(self._ids_type, self._ndims)


def create_leaf_container(name, data_type, **kwargs):
    """Wrapper to create IDSPrimitive/IDSNumericArray from IDS syntax"""
    if data_type == "int_type":
        ids_type = "INT"
        ndims = 0
    elif data_type == "flt_type":
        ids_type = "FLT"
        ndims = 0
    elif data_type == "flt_1d_type":
        ids_type = "FLT"
        ndims = 1
    else:
        ids_type, ids_dims = data_type.split("_")
        ndims = int(ids_dims[:-1])
    if ndims == 0:
        leaf = IDSPrimitive(name, ids_type, ndims, **kwargs)
    else:
        if ids_type == "STR":
            # Array of strings should behave more like lists
            # this is an assumption on user expectation!
            leaf = IDSPrimitive(name, ids_type, ndims, **kwargs)
        else:
            leaf = IDSNumericArray(name, ids_type, ndims, **kwargs)
    return leaf


class IDSNumericArray(IDSPrimitive, np.lib.mixins.NDArrayOperatorsMixin):
    def __str__(self):
        return self.value.__str__()

    # One might also consider adding the built-in list type to this
    # list, to support operations like np.add(array_like, list)
    _HANDLED_TYPES = (np.ndarray, numbers.Number)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        out = kwargs.get("out", ())
        for x in inputs + out:
            # Only support operations with instances of _HANDLED_TYPES.
            # Use ArrayLike instead of type(self) for isinstance to
            # allow subclasses that don't override __array_ufunc__ to
            # handle ArrayLike objects.
            if not isinstance(x, self._HANDLED_TYPES + (IDSPrimitive,)):
                return NotImplemented

        # Defer to the implementation of the ufunc on unwrapped values.
        inputs = tuple(x.value if isinstance(x, IDSPrimitive) else x for x in inputs)
        if out:
            kwargs["out"] = tuple(
                x.value if isinstance(x, IDSPrimitive) else x for x in out
            )
        result = getattr(ufunc, method)(*inputs, **kwargs)

        if type(result) is tuple:
            # multiple return values
            return tuple(
                type(self)(self._name, self._ids_type, self._ndims, value=x)
                for x in result
            )
        elif method == "at":
            # no return value
            return None
        else:
            # one return value
            return type(self)(self._name, self._ids_type, self._ndims, value=result)


class IDSRoot:
    """ Root of IDS tree. Contains all top-level IDSs """

    depth = 0
    path = ""

    @loglevel
    def __init__(self, s=-1, r=-1, rs=None, rr=None, xml_path=None):
        """Initialize a imaspy IDS tree

        Dynamically build the imaspy IDS tree from the given xml path.
        This does not need necessarily need any associated backend,
        but the structure matches MDSPlus pulsefile. E.g. each Root
        is identified by its shot and run, combining into a UID that
        should be unique per database.
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

        # Parse given xml_path and build imaspy IDS structures
        XMLtreeIDSDef = ET.parse(xml_path)
        root = XMLtreeIDSDef.getroot()
        self._children = []
        logger.info(
            "Generating IDS structures from XML file {!s}".format(
                os.path.abspath(xml_path)
            )
        )
        for ids in root:
            my_name = ids.get("name")
            # Only build for equilibrium to KISS
            if my_name not in ["equilibrium", "nbi"]:
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

        status = 0
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
        self, user, tokamak, version, silent=False, options="", ual_version=None
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


class IDSStructure(IDSMixin):
    """IDS structure node

    Represents a node in the IDS tree. Does not itself contain data,
    but contains references to leaf nodes with data (IDSPrimitive) or
    other node-like structures, for example other IDSStructures or
    IDSStructArrays
    """

    _MAX_OCCURRENCES = None

    def getNodeType(self):
        raise NotImplementedError("{!s}.getNodeType()".format(self))
        return NODE_TYPE_STRUCTURE

    # def __deepcopy__(self, memo):
    #    raise NotImplementedError

    # def __copy__(self):
    #    raise NotImplementedError
    @loglevel
    def __init__(self, parent, name, structure_xml):
        """Initialize IDSStructure from XML specification

        Initializes in-memory an IDSStructure. The XML should contain
        all direct descendants of the node. To avoid duplication,
        none of the XML structure is saved directly, so this transformation
        might be irreversible.

        Args:
          - parent: Parent structure. Can be anything, but at database write
                    time should be something with a path attribute
          - name: Name of the node itself. Will be used in path generation when
                  stored in DB
          - structure_xml: Object describing the structure of the IDS. Usually
                           an instance of `xml.etree.ElementTree.Element`
        """
        # To ease setting values at this stage, do not try to cast values
        # to canonical forms
        self._convert_ids_types = False
        self._name = name
        self._base_path = name
        self._children = []  # Store the children as a list of strings.
        # As we cannot restore the parent from just a string, save a reference
        # to the parent. Take care when (deep)copying this!
        self._parent = parent
        self._coordinates = {
            attr: structure_xml.attrib[attr]
            for attr in structure_xml.attrib
            if attr.startswith("coordinate")
        }
        # Loop over the direct descendants of the current node.
        # Do not loop over grandchildren, that is handled by recursiveness.
        for child in structure_xml.getchildren():
            my_name = child.get("name")
            dbg_str = " " * (self.depth + 1) + "- " + my_name
            logger.debug("{:42.42s} initialization".format(dbg_str))
            self._children.append(my_name)
            # Decide what to do based on the data_type attribute
            my_data_type = child.get("data_type")
            if my_data_type == "structure":
                child_hli = IDSStructure(self, my_name, child)
                setattr(self, my_name, child_hli)
            elif my_data_type == "struct_array":
                child_hli = IDSStructArray(self, my_name, child)
                setattr(self, my_name, child_hli)
            else:
                # If it is not a structure or struct_array, it is probably a
                # leaf node. Just naively try to generate one
                tbp = child.get("timebasepath")
                if tbp is not None:
                    logger.critical(
                        "Found a timebasepath of {!s}! Should not happen".format(tbp)
                    )
                coordinates = {
                    attr: child.attrib[attr]
                    for attr in child.attrib
                    if attr.startswith("coordinate")
                }
                setattr(
                    self,
                    my_name,
                    create_leaf_container(
                        my_name, my_data_type, parent=self, coordinates=coordinates
                    ),
                )
        # After initialization, always try to convert setting attributes on this structure
        self._convert_ids_types = True

    @property
    def depth(self):
        """Calculate the depth of the leaf node"""
        my_depth = 0
        if hasattr(self, "_parent"):
            my_depth += 1 + self._parent.depth
        return my_depth

    def copyValues(self, ids):
        """ Not sure what this should do. Well, copy values of a structure!"""
        raise NotImplementedError("{!s}.copyValues(ids)".format(self))

    def __str__(self):
        return '%s("%s")' % (type(self).__name__, self._name)

    def __getitem__(self, key):
        keyname = str(key)
        return getattr(self, keyname)

    def __setitem__(self, key, value):
        keyname = str(key)
        self.__setattr__(keyname, value)

    def __setattr__(self, key, value):
        """
        'Smart' setting of attributes. To be able to warn the user on imaspy
        IDS interaction time, instead of on database put time
        Only try to cast user-facing attributes, as core developers might
        want to always bypass this mechanism (I know I do!)
        """
        # TODO: Check if this heuristic is sufficient
        if (
            not key.startswith("_")
            and hasattr(self, "_convert_ids_types")
            and self._convert_ids_types
        ):
            # Convert IDS type on set time. Never try this for hidden attributes!
            if hasattr(self, key):
                attr = getattr(self, key)
            else:
                # Structure does not exist. It should have been pre-generated
                raise NotImplementedError("generating new structure from scratch")
                attr = create_leaf_container(key, no_data_type_I_guess, parent=self)
            if isinstance(attr, IDSStructure) and not isinstance(value, IDSStructure):
                raise Exception(
                    "Trying to set structure field {!s} with non-structure.".format(key)
                )

            try:
                attr.value = value
            except Exception as ee:
                raise
            else:
                object.__setattr__(self, key, attr)
        else:
            object.__setattr__(self, key, value)

    @loglevel
    def readTime(self, occurrence):
        raise NotImplementedError("{!s}.readTime(occurrence)".format(self))
        time = []
        path = None
        if occurrence == 0:
            path = self._name
        else:
            path = self._name + "/" + str(occurrence)

        status, ctx = self._ull.ual_begin_global_action(self._idx, path, READ_OP)
        if status != 0:
            raise ALException(
                "Error calling ual_begin_global_action() in readTime() operation",
                status,
            )

        status, time = self._ull.ual_read_data_array(
            ctx, "time", "/time", DOUBLE_DATA, 1
        )
        if status != 0:
            raise ALException("ERROR: TIME cannot be read.", status)
        status = self._ull.ual_end_action(ctx)
        if status != 0:
            raise ALException(
                "Error calling ual_end_action() in readTime() operation", status
            )
        return time

    @loglevel
    def get(self, ctx, homogeneousTime):
        """Get data from UAL backend storage format and overwrite data in node

        Tries to dynamically build all needed information for the UAL.
        """
        if len(self._children) == 0:
            logger.warning(
                'Trying to get structure "{!s}" with 0 children'.format(self._name)
            )
        for child_name in self._children:
            dbg_str = " " * self.depth + "- " + child_name
            logger.debug("{:53.53s} get".format(dbg_str))
            child = getattr(self, child_name)
            if isinstance(child, IDSStructure):
                child.get(ctx, homogeneousTime)
                continue  # Nested struct will handle setting attributes
            if isinstance(child, IDSPrimitive):
                status, data = child.get(ctx, homogeneousTime)
            else:
                logger.critical(
                    "Unknown type {!s} for field {!s}! Skipping".format(
                        type(child), child_name
                    )
                )
            if status == 0 and data is not None:
                setattr(self, child_name, data)
            elif status != 0:
                logger.critical(
                    "Unable to get simple field {!s}, UAL return code {!s}".format(
                        child_name, status
                    )
                )
            else:
                logger.debug(
                    "Unable to get simple field {!s}, seems empty".format(child_name)
                )

    @loglevel
    def getSlice(
        self, time_requested, interpolation_method, occurrence=0, data_store=None
    ):
        # Retrieve full IDS data from the open database.
        raise NotImplementedError(
            "{!s}.getSlice(time_requested, interpolation_method, occurrence=0, data_store=None)".format(
                self
            )
        )

    @loglevel
    def _getData(self, ctx, homogeneousTime, nodePath, analyzeTime):
        """ A deeped way of getting data?? using 'traverser' whatever that is """
        raise NotImplementedError(
            "{!s}._getData(ctx, homogeneousTime, nodePath, analyzeTime)".format(self)
        )

    @loglevel
    def put(self, ctx, homogeneousTime):
        """Put data into UAL backend storage format

        As all children _should_ support being put, just call `put` blindly.
        """
        if len(self._children) == 0:
            logger.warning(
                "Trying to put structure {!s} without children to data store".format(
                    self._name
                )
            )
        for child_name in self._children:
            child = getattr(self, child_name)
            dbg_str = " " * self.depth + "- " + child_name
            if child is not None:
                if not isinstance(child, IDSPrimitive):
                    logger.debug("{:53.53s} put".format(dbg_str))
                child.put(ctx, homogeneousTime)

    @loglevel
    def putSlice(self, ctx, homogeneousTime):
        # Store IDS data time slice to the open database.
        raise NotImplementedError("{!s}.putSlice(ctx, homogeneousTime)".format(self))

    def setPulseCtx(self, ctx):
        raise DeprecationWarning(
            "IDSs should not set context directly, set on Root node instead"
        )

    def getPulseCtx(self):
        raise DeprecationWarning(
            "IDSs should not set context directly, set on Root node instead"
        )

    @loglevel
    def delete(self, ctx):
        """Delete data from UAL backend storage"""
        for child_name in self._children:
            child = getattr(self, child_name)
            dbg_str = " " * self.depth + "- " + child_name
            logger.debug("{:53.53s} del".format(dbg_str))
            rel_path = child.getRelCTXPath(ctx)
            if isinstance(child, (IDSStructArray, IDSPrimitive)):
                status = self._ull.ual_delete_data(ctx, rel_path)
                if status != 0:
                    raise ALException(
                        'ERROR: ual_delete_data failed for "{!s}". Status code {!s}'.format(
                            rel_path + "/" + child_name
                        ),
                        status,
                    )
            else:
                status = child.delete(ctx)
                if status != 0:
                    raise ALException(
                        'ERROR: delete failed for "{!s}". Status code {!s}'.format(
                            rel_path + "/" + child_name
                        ),
                        status,
                    )
        return 0


class IDSStructArray(IDSStructure, IDSMixin):
    """IDS array of structures (AoS) node

    Represents a node in the IDS tree. Does not itself contain data,
    but contains references to IDSStructures
    """

    def getAOSPath(self, ignore_nbc_change=1):
        raise NotImplementedError("{!s}.getAOSPath(ignore_nbc_change=1)".format(self))

    @staticmethod
    def getAoSElement(self):
        logger.warning(
            "getAoSElement is deprecated, you should never need this", FutureWarning
        )
        return copy.deepcopy(self._element_structure)

    @staticmethod
    def getBackendInfo(parentCtx, index, homogeneousTime):  # Is this specific?
        raise NotImplementedError(
            "{!s}.getBackendInfo(parentCtx, index, homogeneousTime)".format(self)
        )

    def __init__(self, parent, name, structure_xml, base_path_in="element"):
        """Initialize IDSStructArray from XML specification

        Initializes in-memory an IDSStructArray. The XML should contain
        all direct descendants of the node. To avoid duplication,
        none of the XML structure is saved directly, so this transformation
        might be irreversible.

        Args:
          - parent: Parent structure. Can be anything, but at database write
                    time should be something with a path attribute
          - name: Name of the node itself. Will be used in path generation when
                  stored in DB
          - structure_xml: Object describing the structure of the IDS. Usually
                           an instance of `xml.etree.ElementTree.Element`
        """
        self._base_path = base_path_in
        self._convert_ids_types = False
        self._name = name
        self._parent = parent
        self._coordinates = {
            attr: structure_xml.attrib[attr]
            for attr in structure_xml.attrib
            if attr.startswith("coordinate")
        }
        # Save the converted structure_xml for later reference, and adding new
        # empty structures to the AoS
        self._element_structure = IDSStructure(self, name + "_el", structure_xml)
        # Do not try to convert ids_types by default.
        # As soon as a copy is made, set this to True
        self._element_structure._convert_ids_types = (
            False  # Enable converting after copy
        )
        # Do not store a reference to the parent. We will set this explicitly
        # each time a new instance is created, as all instances share the same
        # parent, this structure itself.
        self._element_structure._parent = None

        # Initialize with an 0-lenght list
        self.value = []

        self._convert_ids_types = True

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def __getattr__(self, key):
        object.__getattribute__(self, key)

    def __getitem__(self, item):
        # value is a list, so the given item should be convertable to integer
        list_idx = int(item)
        return self.value[list_idx]

    def __setitem__(self, item, value):
        # value is a list, so the given item should be convertable to integer
        list_idx = int(item)
        if hasattr(self, "_convert_ids_types") and self._convert_ids_types:
            # Convert IDS type on set time. Never try this for hidden attributes!
            if list_idx in self.value:
                struct = self.value[list_idx]
                try:
                    struct.value = value
                except Exception as ee:
                    raise
        self.value[list_idx] = value

    def append(self, elt):
        """Append elements to the end of the array of structures.

        Parameters
        ----------
        """
        if not isinstance(elt, list):
            elements = [elt]
        else:
            elements = elt
        for e in elements:
            # Just blindly append for now
            # TODO: Maybe check if user is not trying to append weird elements
            self.value.append(e)

    def resize(self, nbelt, keep=False):
        """Resize an array of structures.

        Parameters
        ----------
        nbelt : int
            The number of elements for the targeted array of structure,
            which can be smaller or bigger than the size of the current
            array if it already exists.
        keep : bool, optional
            Specifies if the targeted array of structure should keep
            existing data in remaining elements after resizing it.
        """
        if not keep:
            self.value = []
        cur = len(self.value)
        if nbelt > cur:
            new_els = []
            for ii in range(nbelt - cur):
                new_el = copy.deepcopy(self._element_structure)
                new_el._parent = self
                new_el._convert_ids_types = True
                new_els.append(new_el)
            self.append(new_els)
        elif nbelt < cur:
            raise NotImplementedError("Making IDSStructArrays smaller")
            for i in range(nbelt, cur):
                self.value.pop()
        elif not keep:  # case nbelt = cur
            raise NotImplementedError("Overwriting IDSStructArray elements")
            self.append(
                [
                    process_charge_state__structArrayElement(self._base_path)
                    for i in range(nbelt)
                ]
            )

    def _getData(
        self, aosCtx, indexFrom, indexTo, homogeneousTime, nodePath, analyzeTime
    ):
        raise NotImplementedError(
            "{!s}._getData(aosCtx, indexFrom, indexTo, homogeneousTime, nodePath, analyzeTime)".format(
                self
            )
        )

    @loglevel
    def get(self, parentCtx, homogeneousTime):
        """Get data from UAL backend storage format and overwrite data in node

        Tries to dynamically build all needed information for the UAL.
        """
        timeBasePath = self.getTimeBasePath(homogeneousTime, 0)
        nodePath = self.getRelCTXPath(parentCtx)
        status, aosCtx, size = self._ull.ual_begin_arraystruct_action(
            parentCtx, nodePath, timeBasePath, 0
        )
        if status < 0:
            raise ALException(
                'ERROR: ual_begin_arraystruct_action failed for "process/products/element"',
                status,
            )

        if size < 1:
            return
        if aosCtx > 0:
            context_store[aosCtx] = (
                context_store[parentCtx] + "/" + nodePath + "/" + str(0)
            )
        self.resize(size)
        for i in range(size):
            self.value[i].get(aosCtx, homogeneousTime)
            self._ull.ual_iterate_over_arraystruct(aosCtx, 1)
            context_store.update(
                aosCtx, context_store[parentCtx] + "/" + nodePath + "/" + str(i + 1)
            )  # Update context

        if aosCtx > 0:
            context_store.pop(aosCtx)
            self._ull.ual_end_action(aosCtx)

    def getRelCTXPath(self, ctx):
        """ Get the path relative to given context from an absolute path"""
        if self.path.startswith(context_store[ctx]):
            rel_path = self.path[len(context_store[ctx]) + 1 :]
        else:
            raise Exception("Could not strip context from absolute path")
        return rel_path

    def put(self, parentCtx, homogeneousTime):
        """Put data into UAL backend storage format

        As all children _should_ support being put, just call `put` blindly.
        """
        timeBasePath = self.getTimeBasePath(homogeneousTime)
        # TODO: This might be to simple for array of array of structures
        nodePath = self.getRelCTXPath(parentCtx)
        status, aosCtx, size = self._ull.ual_begin_arraystruct_action(
            parentCtx, nodePath, timeBasePath, len(self.value)
        )
        if status != 0 or aosCtx < 0:
            raise ALException(
                'ERROR: ual_begin_arraystruct_action failed for "{!s}"'.format(
                    self._name
                ),
                status,
            )
        context_store[aosCtx] = context_store[parentCtx] + "/" + nodePath + "/" + str(0)

        for i in range(size):
            # This loops over the whole array
            dbg_str = " " * self.depth + "- [" + str(i) + "]"
            logger.debug("{:53.53s} put".format(dbg_str))
            self.value[i].put(aosCtx, homogeneousTime)
            status = self._ull.ual_iterate_over_arraystruct(aosCtx, 1)
            if status != 0:
                raise ALException(
                    'ERROR: ual_iterate_over_arraystruct failed for "{!s}"'.format(
                        self._name
                    ),
                    status,
                )
            context_store.update(
                aosCtx, context_store[parentCtx] + "/" + nodePath + "/" + str(i + 1)
            )  # Update context

        status = self._ull.ual_end_action(aosCtx)
        context_store.pop(aosCtx)
        if status != 0:
            raise ALException(
                'ERROR: ual_end_action failed for "{!s}"'.format(self._name), status
            )


class IDSToplevel(IDSStructure):
    """This is any IDS Structure which has ids_properties as child node

    At minium, one should fill ids_properties/homogeneous_time
    IF a quantity is filled, the coordinates of that quantity must be filled as well
    """

    @loglevel
    def readHomogeneous(self, occurrence):
        """Read the value of homogeneousTime.

        Returns:
            0: IDS_TIME_MODE_HETEROGENEOUS; Dynamic nodes may be asynchronous, their timebase is located as indicted in the "Coordinates" column of the documentation
            1: IDS_TIME_MODE_HOMOGENEOUS; All dynamic nodes are synchronous, their common timebase is the "time" node that is the child of the nearest parent IDS
            2: IDS_TIME_MODE_INDEPENDENT; No dynamic node is filled in the IDS (dynamic nodes _will_ be skipped by the Access Layer)
        """
        homogeneousTime = IDS_TIME_MODE_UNKNOWN
        if occurrence == 0:
            path = self._name
        else:
            path = self._name + "/" + str(occurrence)

        status, ctx = self._ull.ual_begin_global_action(self._idx, path, READ_OP)
        context_store[ctx] = context_store[self._idx] + "/" + path
        if status != 0:
            raise ALException(
                "Error calling ual_begin_global_action() in readHomogeneous() operation",
                status,
            )

        status, homogeneousTime = self._ull.ual_read_data(
            ctx, "ids_properties/homogeneous_time", "", INTEGER_DATA, 0
        )
        if status != 0:
            raise ALException("ERROR: homogeneous_time cannot be read.", status)
        status = self._ull.ual_end_action(ctx)
        context_store.pop(ctx)
        if status != 0:
            raise ALException(
                "Error calling ual_end_action() in readHomogeneous() operation", status
            )
        return homogeneousTime

    @loglevel
    def read_data_dictionary_version(self, occurrence):
        data_dictionary_version = ""
        path = self._name
        if occurrence != 0:
            path += "/" + str(occurrence)

        status, ctx = self._ull.ual_begin_global_action(self._idx, path, READ_OP)
        context_store[ctx] = context_store[self._idx] + "/" + path
        if status != 0:
            raise ALException(
                "Error calling ual_begin_global_action() in read_data_dictionary_version() operation",
                status,
            )

        status, data_dictionary_version = self._ull.ual_read_data_string(
            ctx, "ids_properties/version_put/data_dictionary", "", CHAR_DATA, 1
        )
        if status != 0:
            raise ALException("ERROR: data_dictionary_version cannot be read.", status)
        status = self._ull.ual_end_action(ctx)
        context_store.pop(ctx)
        if status != 0:
            raise ALException(
                "Error calling ual_end_action() in read_data_dictionary_version() operation",
                status,
            )
        return data_dictionary_version

    @loglevel
    def get(self, occurrence=0, **kwargs):
        """Get data from UAL backend storage format and overwrite data in node

        Tries to dynamically build all needed information for the UAL. As this
        is the root node, it is simple to construct UAL paths and contexts at
        this level. Should have an open database.
        """
        path = None
        if occurrence == 0:
            path = self._name
        else:
            path = self._name + "/" + str(occurrence)

        homogeneousTime = self.readHomogeneous(occurrence)
        if homogeneousTime == IDS_TIME_MODE_UNKNOWN:
            logger.error(
                "Unknown time mode {!s}, stop getting of {!s}".format(
                    homogeneousTime, self._name
                )
            )
            return
        data_dictionary_version = self.read_data_dictionary_version(occurrence)

        # TODO: Do not use global context
        status, ctx = self._ull.ual_begin_global_action(self._idx, path, READ_OP)
        if status != 0:
            raise ALException(
                "Error calling ual_begin_global_action() for {!s}".format(self._name),
                status,
            )
        context_store[ctx] = context_store[self._idx] + path

        logger.debug("{:53.53s} get".format(self._name))
        super().get(ctx, homogeneousTime, **kwargs)

        status = self._ull.ual_end_action(ctx)
        context_store.pop(ctx)
        if status != 0:
            raise ALException(
                "Error calling ual_end_action() for {!s}".format(self._name), status
            )

    @loglevel
    def deleteData(self, occurrence=0):
        """Delete UAL backend storage data

        Tries to dynamically build all needed information for the UAL. As this
        is the root node, it is simple to construct UAL paths and contexts at
        this level. Should have an open database.
        """
        if not np.issubdtype(type(occurrence), np.integer):
            raise ValuError("Occurrence should be an integer")

        rel_path = self.getRelCTXPath(self._idx)
        if occurrence != 0:
            rel_path += "/" + str(occurrence)

        status, ctx = self._ull.ual_begin_global_action(self._idx, rel_path, WRITE_OP)
        context_store[ctx] = context_store[self._idx] + rel_path
        if status < 0:
            raise ALException(
                'ERROR: ual_begin_global_action failed for "{!s}"'.format(rel_path),
                status,
            )

        for child_name in self._children:
            child = getattr(self, child_name)
            if isinstance(child, (IDSStructArray, IDSPrimitive)):
                status = self._ull.ual_delete_data(ctx, child_name)
                if status != 0:
                    raise ALException(
                        'ERROR: ual_delete_data failed for "{!s}". Status code {!s}'.format(
                            rel_path + "/" + child_name
                        ),
                        status,
                    )
            else:
                status = child.delete(ctx)
                if status != 0:
                    raise ALException(
                        'ERROR: delete failed for "{!s}". Status code {!s}'.format(
                            rel_path + "/" + child_name
                        ),
                        status,
                    )
        status = self._ull.ual_end_action(ctx)
        context_store.pop(ctx)
        if status < 0:
            raise ALException(
                'ERROR: ual_end_action failed for "{!s}"'.format(rel_path), status
            )
        return 0

    @loglevel
    def to_ualstore(self, ual_data_store, path=None, occurrence=0):
        """Put data into UAL backend storage format

        As all children _should_ support being put, just call `put` blindly.

        Tries to dynamically build all needed information for the UAL. As this
        is the root node, it is simple to construct UAL paths and contexts at
        this level. Should have an open database.
        """
        if path is not None:
            raise NotImplementedError("Explicit paths, implicitly handled by structure")

        path = self.path
        if occurrence != 0:
            path += "/" + str(occurrence)

        # Determine the time_mode.
        homogeneousTime = self.ids_properties.homogeneous_time.value
        if homogeneousTime == IDS_TIME_MODE_UNKNOWN:
            logger.warning(
                "IDS {!s} is found to be EMPTY (homogeneous_time undefined). PUT quits with no action."
            )
            return
        if homogeneousTime not in IDS_TIME_MODES:
            raise ALException(
                "ERROR: ids_properties.homogeneous_time should be set to IDS_TIME_MODE_HETEROGENEOUS, IDS_TIME_MODE_HOMOGENEOUS or IDS_TIME_MODE_INDEPENDENT."
            )
        if homogeneousTime == IDS_TIME_MODE_HOMOGENEOUS and len(self.time.value) == 0:
            raise ALException(
                "ERROR: the IDS%time vector of an homogeneous_time IDS must have a non-zero length."
            )

        # Delete the data in the store
        # TODO: handle mode correctly!
        self.deleteData(occurrence)

        # Begin a write action
        status, ctx = self._ull.ual_begin_global_action(self._idx, path, WRITE_OP)
        if status != 0:
            raise ALException(
                "Error calling ual_begin_global_action() for {!s}".format(
                    self._name, status
                )
            )

        context_store[ctx] = path
        for child_name in self._children:
            child = getattr(self, child_name)
            dbg_str = " " * self.depth + "- " + child_name
            if not isinstance(child, IDSPrimitive):
                logger.debug("{:53.53s} put".format(dbg_str))
            child.put(ctx, homogeneousTime)

        context_store.pop(ctx)
        status = self._ull.ual_end_action(ctx)
        if status != 0:
            raise ALException(
                "Error calling ual_end_action() for {!s}".format(self._name), status
            )

    def setExpIdx(self, idx):
        logger.warning(
            "setExpIdx is deprecated, call self.setPulseCtx instead", FutureWarning
        )
        self.setPulseCtx(idx)

    @loglevel
    def put(self, occurrence=0, data_store=None):
        if data_store is None:
            data_store = self._data_store
        self.to_ualstore(data_store, path=None, occurrence=occurrence)

    @property
    def _data_store(self):
        return self._parent._data_store

    @property
    def _idx(self):
        return self._data_store._idx

    @classmethod
    def getMaxOccurrences(self):
        raise NotImplementedError("{!s}.getMaxOccurrences()".format(self))
        return cls._MAX_OCCURRENCES

    def initIDS(self):
        raise NotImplementedError("{!s}.initIDS()".format(self))

    def partialGet(self, dataPath, occurrence=0):
        raise NotImplementedError(
            "{!s}.partialGet(dataPath, occurrence=0)".format(self)
        )

    def getField(self, dataPath, occurrence=0):
        raise NotImplementedError("{!s}.getField(dataPath, occurrence=0)".format(self))

    def _getFromPath(self, dataPath, occurrence, analyzeTime, data_store=None):
        # Retrieve partial IDS data without reading the full database content
        raise NotImplementedError(
            "{!s}.getField(dataPath, occurrence, analyzeTime, data_store=None)".format(
                self
            )
        )
