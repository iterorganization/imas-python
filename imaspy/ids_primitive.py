# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Core IDS classes

Provides the class for an IDS Primitive data type

* :py:class:`IDSPrimitive`
"""

import logging
import numbers

import numpy as np

from imaspy.setup_logging import root_logger as logger
from imaspy.al_exception import ALException
from imaspy.context_store import context_store
from imaspy.ids_defs import DD_TYPES
from imaspy.ids_mixin import IDSMixin

try:
    from imaspy.ids_defs import (
        CHAR_DATA,
        DOUBLE_DATA,
        INTEGER_DATA,
        COMPLEX_DATA,
        hli_utils,
        ids_type_to_default,
    )
except ImportError:
    logger.critical("IMAS could not be imported. UAL not available!")


class IDSPrimitive(IDSMixin):
    """IDS leaf node

    Represents actual data. Examples are (arrays of) strings, floats, integers.
    Lives entirely in-memory until 'put' into a database.
    """

    def __init__(
        self,
        name,
        ids_type,
        ndims,
        parent=None,
        value=None,
        coordinates=None,
        structure_xml=None,
        var_type="dynamic",
    ):
        """Initialize IDSPrimitive

        Args:
            name: Name of the leaf node. Will be used in path generation when
                stored in DB
            ids_type: String representing the IDS type. Will be used to convert
                to Python equivalent
            ndims: Dimensionality of data
            parent: Parent node of this leaf. Can be anything with a _path attribute.
                Will be used in path generation when stored in DB
            value: Value to fill the leaf with. Can be anything castable by
                IDSPrimitive.cast_value. If not given, will be filled by
                default data matching given ids_type and ndims
            coordinates: Data coordinates of the node
            var_type: 'static', 'dynamic', or 'const'
        """
        # Devnote. As IDSNumericArray uses this __init__, and IDSNumericArray
        # subclasses np.lib.mixins.NDArrayOperatorsMixin, copy the call
        # signature of np.lib.mixins.NDArrayOperatorsMixins __init__ to
        # let IDSNumericArray act as a numpy array
        super().__init__(
            parent,
            name,
            coordinates=coordinates,
            structure_xml=structure_xml,
        )

        if ids_type != "STR" and ndims != 0 and self.__class__ == IDSPrimitive:
            raise Exception(
                "{!s} should be 0D! Got ndims={:d}. "
                "Instantiate using IDSNumericArray instead".format(
                    self.__class__, ndims
                )
            )

        self.__value = value
        self._ids_type = ids_type
        self._var_type = var_type
        self._ndims = ndims
        self._backend_type = None
        self._backend_ndims = None

    @property
    def has_value(self):
        """True if a value is defined here"""
        return self.__value is not None

    @property
    def _default(self):
        if self._ndims == 0:
            return ids_type_to_default[self._ids_type]
        return np.full((0,) * self._ndims, ids_type_to_default[self._ids_type])

    def __iter__(self):
        return iter([])

    @property
    def value(self):
        """Return the value of this IDSPrimitive if it is set,
        otherwise return the default"""
        if self.__value is None:
            return self._default
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

    def __eq__(self, other):
        if isinstance(other, IDSPrimitive):
            ref = other.value
        else:
            ref = other

        if self._ndims >= 1:
            return np.array_equal(self.value, ref)
        else:
            return self.value == ref

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
        elif self._ids_type == "CPX" and self._ndims == 0:
            value = complex(value)
        elif self._ndims >= 1:
            if self._ids_type == "FLT":
                value = np.array(value, dtype=np.float64)
            elif self._ids_type == "CPX":
                value = np.array(value, dtype=np.complex128)
            elif self._ids_type == "INT":
                value = np.array(value, dtype=np.int64)
            elif self._ids_type == "STR":
                # make sure that all the strings are decoded
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
                    "Unknown numpy type %s, cannot convert from python to IDS type",
                    value.dtype,
                )
                raise Exception
        else:
            logger.critical(
                "Unknown python type %s, cannot convert from python to IDS type",
                type(value),
            )
            raise Exception
        return value

    @staticmethod
    def parse_data(name, ndims, write_type, value):
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
                value = round(value)
            elif write_type == "FLT":
                value = float(value)
            data = value
        elif write_type in ["INT", "FLT", "CPX"]:
            # Arrays will be converted by isTypeValid
            if not hli_utils.HLIUtils.isTypeValid(value, name, "NP_ARRAY"):
                raise Exception
            data = value
        else:
            # TODO: convert data on write time here
            if write_type == "INT":
                data = round(value)
            elif write_type == "FLT":
                data = float(value)
            else:
                data = value
        return data

    @staticmethod
    def data_is_default(data, default):
        # Do not write if data is the same as the default of the leaf node
        # TODO: set default of backend xml instead
        if isinstance(data, (list, np.ndarray)):
            if len(data) == 0 or np.array_equal(
                np.asarray(data), np.asarray(default)
            ):
                return True
            # we need the extra asarray to convert the list back to an np ndarray
        elif data == default:
            return True
        return False

    def put(self, ctx, homogeneousTime, **kwargs):
        """Put data into UAL backend storage format

        Does minor sanity checking before calling the cython backend.
        Tries to dynamically build all needed information for the UAL.
        """
        if self._name is None:
            raise Exception("Location in tree undefined, cannot put in database")
        if "types" in kwargs:
            if self._var_type not in kwargs["types"]:
                logger.debug(
                    "Skipping write of %s because var_type %s not in %s",
                    self._name,
                    self._var_type,
                    kwargs["types"],
                )
                return
        write_type = self._backend_type or self._ids_type
        ndims = self._backend_ndims or self._ndims
        data = self.parse_data(self._name, ndims, write_type, self.value)

        if self.data_is_default(data, self._default):
            return

        # Call signature
        # ual_write_data(ctx, pyFieldPath, pyTimebasePath, inputData, dataType=0, dim = 0, sizeArray = np.empty([0], dtype=np.int32))
        # data_type = self._ull._getDataType(data)

        # Strip context from absolute path
        rel_path = self.getRelCTXPath(ctx)
        # TODO: Check ignore_nbc_change
        strTimeBasePath = self.getTimeBasePath(homogeneousTime)

        if logger.level <= logging.DEBUG:
            log_string = " " * self.depth + " - % -38s write"
            logger.debug(log_string, "/".join([context_store[ctx], rel_path]))

        # TODO: the data_type argument seems to be unused in the ual_write_data routine, remove it?
        status = self._ull.ual_write_data(
            ctx, rel_path, strTimeBasePath, data, dataType=write_type, dim=ndims
        )
        if status != 0:
            raise ALException('Error writing field "{!s}"'.format(self._name))

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
        elif read_type == "CPX" and ndims == 0:
            status, data = self._ull.ual_read_data_scalar(
                ctx, strNodePath, strTimeBasePath, COMPLEX_DATA
            )
        elif read_type == "FLT" and ndims > 0:
            status, data = self._ull.ual_read_data_array(
                ctx, strNodePath, strTimeBasePath, DOUBLE_DATA, self._ndims
            )
        elif read_type == "INT" and ndims > 0:
            status, data = self._ull.ual_read_data_array(
                ctx, strNodePath, strTimeBasePath, INTEGER_DATA, self._ndims
            )
        elif read_type == "CPX" and ndims > 0:
            status, data = self._ull.ual_read_data_array(
                ctx, strNodePath, strTimeBasePath, COMPLEX_DATA, self._ndims
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
        return '%s("%s", %r)' % (type(self).__name__, self._path, self.value)

    @property
    def data_type(self):
        """Combine imaspy ids_type and ndims to UAL data_type"""
        return "{!s}_{!s}D".format(self._ids_type, self._ndims)

    def set_backend_properties(self, xml_child):
        """Set the backend properties on this IDSPrimitive"""

        if xml_child is None:
            logger.warning(
                "Field %s in memory rep not found in backend xml, "
                "will not be written",
                self._path,
            )
            data_type = None
            return

        data_type = xml_child.get("data_type")

        # this ensures that even if this self does not exist in backend_xml
        # we set the backend_type to None (otherwise you could have bugs
        # when switching backend_xml multiple times)
        if data_type:
            self._backend_type, self._backend_ndims = DD_TYPES[data_type]
        else:
            self._backend_type = None
            self._backend_ndims = None

        # only set backend name if different from name
        if xml_child.get("name") != self._name:
            self._backend_name = xml_child.get("name")
        else:
            self._backend_name = None

        if self._backend_name:
            logger.info(
                "Setting up mapping from %s (mem) to %s (file)",
                self._name,
                self._path,
            )

        if self._backend_type != self._ids_type:
            logger.info(
                "Setting up conversion at %s, memory=%s, backend=%s",
                self._path,
                self._ids_type,
                self._backend_type,
            )
        if self._backend_ndims != self._ndims:
            logger.error(
                "Dimensions mismatch at %s, memory=%s, backend=%s",
                self._path,
                self._ndims,
                self._backend_ndims,
            )


def create_leaf_container(name, data_type, **kwargs):
    """Wrapper to create IDSPrimitive/IDSNumericArray from IDS syntax.
    TODO: move this elsewhere.
    """
    ids_type, ndims = DD_TYPES[data_type]
    # legacy support
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

    def resize(self, new_shape):
        """Resize underlying data

        Data is stored in memory in a numpy array, so use numpy's resize to
        resize the underlying data
        """
        self.value.resize(new_shape)
