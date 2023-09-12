# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" Core IDS classes

Provides the class for an IDS Primitive data type

* :py:class:`IDSPrimitive`
"""
import logging
import numbers
from typing import Any, Dict, Tuple
from xml.etree.ElementTree import Element

import numpy as np

from imaspy.ids_coordinates import IDSCoordinates
from imaspy.ids_data_type import IDSDataType
from imaspy.ids_defs import hli_utils
from imaspy.ids_mixin import IDSMixin


logger = logging.getLogger(__name__)


class IDSPrimitive(IDSMixin):
    """IDS leaf node

    Represents actual data. Examples are (arrays of) strings, floats, integers.
    Lives entirely in-memory until 'put' into a database.
    """

    def __init__(
        self,
        parent: IDSMixin,
        structure_xml: Element,
        value: Any = None,
        var_type: str = "dynamic",
    ):
        """Initialize IDSPrimitive

        Args:
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
        super().__init__(parent, structure_xml=structure_xml)
        self.coordinates = IDSCoordinates(self)

        if (
            self.metadata.data_type is not IDSDataType.STR
            and self.metadata.ndim != 0
            and self.__class__ == IDSPrimitive
        ):
            raise ValueError(
                "{!s} should be 0D! Got ndims={:d}. "
                "Instantiate using IDSNumericArray instead".format(
                    self.__class__, self.metadata.ndim
                )
            )

        self.__value = value
        self._var_type = var_type
        self._backend_type = None
        self._backend_ndims = None

    @property
    def shape(self) -> Tuple[int, ...]:
        """Get the shape of the contained data.

        For 0D data types, the shape is always an empty tuple.
        See also :external:py:meth:`numpy.shape`.
        """
        if self.metadata.ndim == 0:
            return tuple()
        if self.__value is None:
            return (0,) * self.metadata.ndim
        return np.shape(self.__value)

    @property
    def size(self) -> int:
        """Get the size of stored data (number of elements stored).

        For 0D data types, the size is always 1 (even when set to the default).
        For 1+D data types, the size is the number of elements stored, see
        :external:py:meth:`numpy.ndarray.size`.
        """
        if self.metadata.ndim == 0:
            return 1
        if self.__value is None:
            return 0
        if self.metadata.data_type == IDSDataType.STR:
            return len(self.__value)
        # self.__value must be a numpy array
        return self.__value.size

    @property
    def has_value(self) -> bool:
        """True if a value is defined here that is not the default"""
        if self.__value is None:  # No value set
            return False
        return self.size > 0  # Default for ndarray and STR_1D types is size == 0

    def __len__(self) -> int:
        if self.metadata.ndim == 0:
            raise TypeError(f"IDS data node of type {self.data_type} has no len()")
        if self.__value is None:
            return 0
        return len(self.__value)

    @property
    def _default(self):
        data_type = self.metadata.data_type
        if self.metadata.ndim == 0:
            return data_type.default
        if data_type is IDSDataType.STR:
            return []
        return np.empty((0,) * self.metadata.ndim, dtype=data_type.numpy_dtype)

    def __iter__(self):
        return iter([])

    def __repr__(self):
        empty = value_repr = ""
        if self.has_value:
            value_repr = f"\n{self.value.__class__.__qualname__}({self.value!r})"
        else:
            empty = "empty "
        return f"{self._build_repr_start()}, {empty}{self.data_type})>{value_repr}"

    @property
    def value(self):
        """Return the value of this IDSPrimitive if it is set,
        otherwise return the default"""
        if self.__value is None:
            if self.metadata.ndim == 0:
                return self._default
            # 1+D data types can be modified in-place, first set before returning so,
            # for example, `ids.time.value.resize(10)`` always works as expected.
            self.__value = self._default
        return self.__value

    @value.setter
    def value(self, setter_value):
        if isinstance(setter_value, type(self)):
            # No need to cast, just overwrite contained value
            if (
                setter_value.metadata.data_type is self.metadata.data_type
                and setter_value.metadata.ndim == self.metadata.ndim
            ):
                self.__value = setter_value.value
            # Can we cast the internal value to a valid value?
            else:
                self.__value = self.cast_value(setter_value.value)
        else:
            self.__value = self.cast_value(setter_value)
        if self.metadata.ndim == 0 and self.__value == self.metadata.data_type.default:
            # Unset 0D types when setting them to their magic default value
            self.__value = None

    def __eq__(self, other):
        if isinstance(other, IDSPrimitive):
            ref = other.value
        else:
            ref = other

        if self.metadata.ndim >= 1:
            return np.array_equal(self.value, ref)
        else:
            return self.value == ref

    def cast_value(self, value):
        # Cast values to their IDS-python types
        logmsg = "Assigning incorrect type '%s' to %r, attempting automatic conversion."
        if self.metadata.data_type is IDSDataType.STR:  # strings are special
            if self.metadata.ndim == 0:
                if not isinstance(value, str):
                    logger.info(logmsg, type(value), self)
                value = _cast_str(value)
            else:  # STR_1D -> List[str]
                if isinstance(value, (tuple, list, np.ndarray)):
                    if not all(isinstance(val, str) for val in value):
                        logger.info(logmsg, value, self)
                    value = list(map(_cast_str, value))
                else:
                    logger.info(logmsg, type(value), self)
                    value = [_cast_str(value)]

        elif self.metadata.ndim == 0:
            type_ = self.metadata.data_type.python_type
            if isinstance(value, np.ndarray) and value.ndim == 0:
                value = value.item()  # Unpack 0D numpy arrays
            if not isinstance(value, type_):
                logger.info(logmsg, type(value), self)
            value = type_(value)

        else:  # ndim >= 1
            dtype = self.metadata.data_type.numpy_dtype
            value = np.asanyarray(value)
            if value.dtype != dtype:
                logger.info(logmsg, value.dtype, self)
            value = np.array(value, dtype=dtype, copy=False)
            if value.ndim != self.metadata.ndim:
                raise ValueError(
                    f"Trying to assign a {value.ndim}D value to {self!r}."
                )

        return value

    @staticmethod
    def parse_data(name, ndims, write_type, value):
        """Parse IDS information to generate a IMASPy data structure.

        Args:
            name: The name of the IDS node, e.g. b0_error_upper
            ndims: Dimensionality of the given data
            write_type: Type as defined in the IDS or backend, e.g. FLT
            value: The value of the data saved in IMASPy
        """
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
                raise RuntimeError(f"Value {value} not valid for field {name}")
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
            if len(data) == 0 or np.array_equal(np.asarray(data), np.asarray(default)):
                return True
            # we need the extra asarray to convert the list back to an np ndarray
        elif data == default:
            return True
        return False

    @property
    def data_type(self):
        """Combine imaspy ids_type and ndims to UAL data_type"""
        return "{!s}_{!s}D".format(self.metadata.data_type.value, self.metadata.ndim)

    def _validate(self) -> None:
        # Common validation logic
        super()._validate()
        # Validate coordinates
        if self.has_value:
            self.coordinates._validate()


def _cast_str(value):
    """Cast a value to a string.

    If value is a bytes object, decode it using UTF-8. Otherwise return str(value).
    """
    return value.decode("UTF-8") if isinstance(value, bytes) else str(value)


def create_leaf_container(parent, structure_xml, **kwargs):
    """Wrapper to create IDSPrimitive/IDSNumericArray from IDS syntax.
    TODO: move this elsewhere.
    """
    ids_type, ndims = IDSDataType.parse(structure_xml.attrib["data_type"])
    # legacy support
    if ndims == 0:
        leaf = IDSPrimitive(parent, structure_xml, **kwargs)
    else:
        if ids_type == "STR":
            # Array of strings should behave more like lists
            # this is an assumption on user expectation!
            leaf = IDSPrimitive(parent, structure_xml, **kwargs)
        else:
            leaf = IDSNumericArray(parent, structure_xml, **kwargs)
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

        if method == "at":
            # no return value
            return None
        else:
            # one return value
            return result

    def resize(self, new_shape):
        """Resize underlying data

        Data is stored in memory in a numpy array, so use numpy's resize to
        resize the underlying data
        """
        self.value.resize(new_shape)

    def __repr__(self):
        # Specify that this is a numpy array, instead of a Python array As we
        # know .value is a numpy array, we can remove "array" part of the
        # numpy-native repr
        empty = value_repr = ""
        if self.has_value:
            value_repr = f"\n{_fullname(self.value)}{repr(self.value)[5:]}"
        else:
            empty = "empty "
        return f"{self._build_repr_start()}, {empty}{self.data_type})>{value_repr}"


def _fullname(o) -> str:
    """Get the full name to a type, including module name etc.

    Examples:
        - _fullname(np.array([1,2,3]) -> numpy.ndarray
        - fullname([1,2,3]) -> list
    """
    class_ = o.__class__
    module = class_.__module__
    if module == "builtins":
        return class_.__qualname__  # avoid outputs like 'builtins.str'
    return module + "." + class_.__qualname__
