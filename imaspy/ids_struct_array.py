# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" IDS StructArray represents an Array of Structures in the IDS tree.
This contains references to :py:class:`IDSStructure`s

* :py:class:`IDSStructArray`
"""


import copy

import numpy as np

from .al_exception import ALException
from .context_store import context_store
from .defs import (
    CHAR_DATA,
    IDS_TIME_MODE_HOMOGENEOUS,
    IDS_TIME_MODE_UNKNOWN,
    IDS_TIME_MODES,
    INTEGER_DATA,
    READ_OP,
    WRITE_OP,
)
from .ids_mixin import IDSMixin
from .ids_primite import IDSPrimitive
from .ids_structure import IDSStructure
from .logger import logger, loglevel


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
        raise NotImplementedError("getBackendInfo(parentCtx, index, homogeneousTime)")

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
                    raise ee
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
            raise ValueError("Occurrence should be an integer")

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
