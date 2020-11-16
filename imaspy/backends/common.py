# BackendArray, AbstractDataStore and AbstractWritableDataStore
# are taken from xarray c07160dd2d627a021e58515cbd7753c11fb56d94
# The following unneeded functions have been removed:
# variables
# attrs
# dimensions
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
from collections.abc import Mapping

import imaspy.backends.xarray_core_indexing as indexing
from imaspy.backends.xarray_core_utils import NdimSizeLenMixin


class BackendArray(NdimSizeLenMixin, indexing.ExplicitlyIndexed):
    __slots__ = ()

    def __array__(self, dtype=None):
        key = indexing.BasicIndexer((slice(None),) * self.ndim)
        return np.asarray(self[key], dtype=dtype)


class AbstractDataStore(Mapping):
    __slots__ = ()

    def __iter__(self):
        return iter(self.variables)

    def __getitem__(self, key):
        return self.variables[key]

    def __len__(self):
        return len(self.variables)

    def get_dimensions(self):  # pragma: no cover
        raise NotImplementedError()

    def get_attrs(self):  # pragma: no cover
        raise NotImplementedError()

    def get_variables(self):  # pragma: no cover
        raise NotImplementedError()

    def get_encoding(self):
        return {}

    def load(self):
        """
        This loads the variables and attributes simultaneously.
        A centralized loading function makes it easier to create
        data stores that do automatic encoding/decoding.

        For example::

            class SuffixAppendingDataStore(AbstractDataStore):

                def load(self):
                    variables, attributes = AbstractDataStore.load(self)
                    variables = {'%s_suffix' % k: v
                                 for k, v in variables.items()}
                    attributes = {'%s_suffix' % k: v
                                  for k, v in attributes.items()}
                    return variables, attributes

        This function will be called anytime variables or attributes
        are requested, so care should be taken to make sure its fast.
        """
        variables = FrozenDict(
            (_decode_variable_name(k), v) for k, v in self.get_variables().items()
        )
        attributes = FrozenDict(self.get_attrs())
        return variables, attributes

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()


class AbstractWritableDataStore(AbstractDataStore):
    __slots__ = ()

    def encode(self, variables, attributes):
        """
        Encode the variables and attributes in this store

        Parameters
        ----------
        variables : dict-like
            Dictionary of key/value (variable name / xr.Variable) pairs
        attributes : dict-like
            Dictionary of key/value (attribute name / attribute) pairs

        Returns
        -------
        variables : dict-like
        attributes : dict-like

        """
        variables = {k: self.encode_variable(v) for k, v in variables.items()}
        attributes = {k: self.encode_attribute(v) for k, v in attributes.items()}
        return variables, attributes

    def encode_variable(self, v):
        """encode one variable"""
        return v

    def encode_attribute(self, a):
        """encode one attribute"""
        return a

    def set_dimension(self, dim, length):  # pragma: no cover
        raise NotImplementedError()

    def set_attribute(self, k, v):  # pragma: no cover
        raise NotImplementedError()

    def set_variable(self, k, v):  # pragma: no cover
        raise NotImplementedError()

    def store_dataset(self, dataset):
        """
        in stores, variables are all variables AND coordinates
        in xarray.Dataset variables are variables NOT coordinates,
        so here we pass the whole dataset in instead of doing
        dataset.variables
        """
        self.store(dataset, dataset.attrs)

    def store(
        self,
        variables,
        attributes,
        check_encoding_set=frozenset(),
        writer=None,
        unlimited_dims=None,
    ):
        """
        Top level method for putting data on this store, this method:
          - encodes variables/attributes
          - sets dimensions
          - sets variables

        Parameters
        ----------
        variables : dict-like
            Dictionary of key/value (variable name / xr.Variable) pairs
        attributes : dict-like
            Dictionary of key/value (attribute name / attribute) pairs
        check_encoding_set : list-like
            List of variables that should be checked for invalid encoding
            values
        writer : ArrayWriter
        unlimited_dims : list-like
            List of dimension names that should be treated as unlimited
            dimensions.
        """
        if writer is None:
            writer = ArrayWriter()

        variables, attributes = self.encode(variables, attributes)

        self.set_attributes(attributes)
        self.set_dimensions(variables, unlimited_dims=unlimited_dims)
        self.set_variables(
            variables, check_encoding_set, writer, unlimited_dims=unlimited_dims
        )

    def set_attributes(self, attributes):
        """
        This provides a centralized method to set the dataset attributes on the
        data store.

        Parameters
        ----------
        attributes : dict-like
            Dictionary of key/value (attribute name / attribute) pairs
        """
        for k, v in attributes.items():
            self.set_attribute(k, v)

    def set_variables(self, variables, check_encoding_set, writer, unlimited_dims=None):
        """
        This provides a centralized method to set the variables on the data
        store.

        Parameters
        ----------
        variables : dict-like
            Dictionary of key/value (variable name / xr.Variable) pairs
        check_encoding_set : list-like
            List of variables that should be checked for invalid encoding
            values
        writer : ArrayWriter
        unlimited_dims : list-like
            List of dimension names that should be treated as unlimited
            dimensions.
        """

        for vn, v in variables.items():
            name = _encode_variable_name(vn)
            check = vn in check_encoding_set
            target, source = self.prepare_variable(
                name, v, check, unlimited_dims=unlimited_dims
            )

            writer.add(source, target)

    def set_dimensions(self, variables, unlimited_dims=None):
        """
        This provides a centralized method to set the dimensions on the data
        store.

        Parameters
        ----------
        variables : dict-like
            Dictionary of key/value (variable name / xr.Variable) pairs
        unlimited_dims : list-like
            List of dimension names that should be treated as unlimited
            dimensions.
        """
        if unlimited_dims is None:
            unlimited_dims = set()

        existing_dims = self.get_dimensions()

        dims = {}
        for v in unlimited_dims:  # put unlimited_dims first
            dims[v] = None
        for v in variables.values():
            dims.update(dict(zip(v.dims, v.shape)))

        for dim, length in dims.items():
            if dim in existing_dims and length != existing_dims[dim]:
                raise ValueError(
                    "Unable to update size for existing dimension"
                    "%r (%d != %d)" % (dim, length, existing_dims[dim])
                )
            elif dim not in existing_dims:
                is_unlimited = dim in unlimited_dims
                self.set_dimension(dim, length, is_unlimited)


class WritableIMASDataStore(AbstractWritableDataStore):
    __slots__ = ()

    def encode(self, variables, attributes):
        # Encode all varibles IMAS-style. Equivalent to xarrays CFDataStore, repeated here
        # for reference:
        # def encode(self, variables, attributes):
        #    variables = {k: self.encode_variable(v) for k, v in variables.items()}
        #    attributes = {k: self.encode_attribute(v) for k, v in attributes.items()}
        #    return variables, attributes
        variables, attributes = imas_encoder(variables, attributes)
        variables = {k: self.encode_variable(v) for k, v in variables.items()}
        attributes = {k: self.encode_attribute(v) for k, v in attributes.items()}
        return variables, attributes
