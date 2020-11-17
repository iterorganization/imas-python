# NdimSizeLenMixin and NDArrayMixin
# are taken from xarray c07160dd2d627a021e58515cbd7753c11fb56d94
#
# This code can be modified if you explicitly note your
# changes. However, it would be better to wrap these
# classes instead
#
#
# Copyright 2014-2020, xarray Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import (
    AbstractSet,
    Any,
    Callable,
    Collection,
    Container,
    Dict,
    Hashable,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSet,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import numpy as np


class NdimSizeLenMixin:
    """Mixin class that extends a class that defines a ``shape`` property to
    one that also defines ``ndim``, ``size`` and ``__len__``.
    """

    __slots__ = ()

    @property
    def ndim(self: Any) -> int:
        return len(self.shape)

    @property
    def size(self: Any) -> int:
        # cast to int so that shape = () gives size = 1
        return int(np.prod(self.shape))

    def __len__(self: Any) -> int:
        try:
            return self.shape[0]
        except IndexError:
            raise TypeError("len() of unsized object")


class NDArrayMixin(NdimSizeLenMixin):
    """Mixin class for making wrappers of N-dimensional arrays that conform to
    the ndarray interface required for the data argument to Variable objects.

    A subclass should set the `array` property and override one or more of
    `dtype`, `shape` and `__getitem__`.
    """

    __slots__ = ()

    @property
    def dtype(self: Any) -> np.dtype:
        return self.array.dtype

    @property
    def shape(self: Any) -> Tuple[int]:
        return self.array.shape

    def __getitem__(self: Any, key):
        return self.array[key]

    def __repr__(self: Any) -> str:
        return "{}(array={!r})".format(type(self).__name__, self.array)
