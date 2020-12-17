# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Core IDS classes

Provides the class for an IDS Primitive data type

* :py:class:`IDSPrimitive`
"""

# Set up logging immediately
import numpy as np
from imaspy.al_exception import ALException
from imaspy.context_store import context_store
from imaspy.ids_mixin import IDSMixin
from imaspy.logger import logger, loglevel

try:
    from imaspy.ids_defs import (
        CHAR_DATA,
        DOUBLE_DATA,
        INTEGER_DATA,
        hli_utils,
        ids_type_to_default,
    )
except:
    logger.critical("IMAS could not be imported. UAL not available!")


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
        self._backend_type = None
        self._backend_ndims = None
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
            elif self._ids_type == "STR":
                # make sure that all the strings are decoded
                # numpy str_ objects are not handled nicely, convert to python list
                if isinstance(value, np.ndarray):
                    value = list(
                        [
                            str(val, encoding="UTF-8")
                            if isinstance(val, bytes)
                            else val
                            for val in value
                        ]
                    )
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
        write_type = self._backend_type or self._ids_type
        ndims = self._backend_ndims or self._ndims

        # Convert imaspy ids_type to ual scalar_type
        if write_type == "INT":
            scalar_type = 1
        elif write_type == "FLT":
            scalar_type = 2
        elif write_type == "CPX":  # TODO: Add CPX to ids_minimal_types.xml
            scalar_type = 3

        # Check sanity of given data
        if write_type in ["INT", "FLT", "CPX"] and ndims == 0:
            # Manually convert value to write_type
            # TODO: bundle these as 'generic' migrations
            if write_type == "INT":
                value = round(self.value)
            elif write_type == "FLT":
                value = float(self.value)
            data = hli_utils.HLIUtils.isScalarFinite(value, scalar_type)
        elif write_type in ["INT", "FLT", "CPX"]:
            # Arrays will be converted by isTypeValid
            if not hli_utils.HLIUtils.isTypeValid(self.value, self._name, "NP_ARRAY"):
                raise Exception
            data = hli_utils.HLIUtils.isFinite(self.value, scalar_type)
        else:
            # TODO: convert data on write time here
            if write_type == "INT":
                data = round(self.value)
            elif write_type == "FLT":
                data = float(self.value)
            else:
                data = self.value

        # Do not write if data is the same as the default of the leaf node
        # TODO: set default of backend xml instead
        if np.all(data == self._default):
            return

        dbg_str = " " + " " * self.depth + "- " + self._name
        dbg_str += (" {:" + str(max(0, 53 - len(dbg_str))) + "s}").format(
            "(" + str(data) + ")"
        )
        # Call signature
        # ual_write_data(ctx, pyFieldPath, pyTimebasePath, inputData, dataType=0, dim = 0, sizeArray = np.empty([0], dtype=np.int32))
        # data_type = self._ull._getDataType(data)

        # Strip context from absolute path
        rel_path = self.getRelCTXPath(ctx)
        # TODO: Check ignore_nbc_change
        strTimeBasePath = self.getTimeBasePath(homogeneousTime)

        logger.info("{:54.54s} write".format(dbg_str))
        logger.debug(
            "   {:50.50s} write".format("/".join([context_store[ctx], rel_path]))
        )
        # TODO: the data_type argument seems to be unused in the ual_write_data routine, remove it?
        status = self._ull.ual_write_data(
            ctx, rel_path, strTimeBasePath, data, dataType=write_type, dim=ndims
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
        read_type = self._backend_type or self._ids_type
        ndims = self._backend_ndims or self._ndims
        # we are not really ready to deal with a change in ndims

        if read_type == "STR" and ndims == 0:
            status, data = self._ull.ual_read_data_string(
                ctx, strNodePath, strTimeBasePath, CHAR_DATA, 1
            )
        elif read_type == "STR" and ndims == 1:
            status, data = self._ull.ual_read_data_array_string(
                ctx,
                strNodePath,
                strTimeBasePath,
                CHAR_DATA,
                2,
            )
        elif read_type == "INT" and ndims == 0:
            status, data = self._ull.ual_read_data_scalar(
                ctx, strNodePath, strTimeBasePath, INTEGER_DATA
            )
        elif read_type == "FLT" and ndims == 0:
            status, data = self._ull.ual_read_data_scalar(
                ctx, strNodePath, strTimeBasePath, DOUBLE_DATA
            )
        elif read_type == "FLT" and ndims > 0:
            status, data = self._ull.ual_read_data_array(
                ctx, strNodePath, strTimeBasePath, DOUBLE_DATA, self._ndims
            )
        elif read_type == "INT" and ndims > 0:
            status, data = self._ull.ual_read_data_array(
                ctx, strNodePath, strTimeBasePath, INTEGER_DATA, self._ndims
            )
        else:
            logger.critical(
                "Unknown type {!s} ndims {!s} of field {!s}, skipping for now".format(
                    read_type, ndims, self._name
                )
            )
            status = data = None

        # TODO: use round() instead of floor() for float -> int
        # this does not actually convert the data, the in-memory representation
        # is the same as the backend representation. Python does the data conversion
        # on comparison time (see test_minimal_conversion.py)
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
    """Wrapper to create IDSPrimitive/IDSNumericArray from IDS syntax.
    TODO: move this elsewhere.
    """
    ids_type, ndims = parse_dd_type(data_type)
    # legacy support
    if ndims == 0:
        leaf = IDSPrimitive(name, ids_type, ndims, **kwargs)
    else:
        if ids_type == "STR":
            # Array of strings should behave more like lists
            # this is an assumption on user expectation!
            leaf = IDSPrimitive(name, ids_type, ndims, **kwargs)
        else:
            # Prevent circular import problems
            from imaspy.ids_numeric_array import IDSNumericArray

            leaf = IDSNumericArray(name, ids_type, ndims, **kwargs)
    return leaf


def parse_dd_type(data_type):
    """Map from data types to ids_type, ids_dims"""
    if data_type == "int_type":
        ids_type = "INT"
        ndims = 0
    elif data_type == "flt_type":
        ids_type = "FLT"
        ndims = 0
    elif data_type == "flt_1d_type":
        ids_type = "FLT"
        ndims = 1
    elif data_type == "str_type":
        ids_type = "STR"
        ndims = 0
    elif data_type == "str_1d_type":
        ids_type = "STR"
        ndims = 1
    else:
        ids_type, ids_dims = data_type.split("_")
        ndims = int(ids_dims[:-1])

    return ids_type, ndims
