# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" IDS StructArray represents an Array of Structures in the IDS tree.
This contains references to :py:class:`IDSStructure`s

* :py:class:`IDSStructArray`
"""


import copy

from imaspy.al_exception import ALException
from imaspy.context_store import context_store
from imaspy.ids_mixin import IDSMixin
from imaspy.ids_structure import IDSStructure
from imaspy.logger import logger


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
        # do not set _parent as it causes loops with deepcopy
        self._element_structure._parent = None
        # instead the append() method will set it

        # Do not try to convert ids_types by default.
        # Instead the append() method will set this
        self._element_structure._convert_ids_types = (
            False  # Enable converting after copy
        )

        # set maxoccur
        self._maxoccur = None
        try:
            self._maxoccur = int(structure_xml.attrib["maxoccur"])
        except ValueError:
            pass
        except KeyError:
            pass

        # Initialize with an 0-length list
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
            if self._maxoccur and len(self.value) >= self._maxoccur:
                raise ValueError(
                    "Maxoccur is set to %s for %s, not adding %s"
                    % (
                        self._maxoccur,
                        self._base_path,
                        elt,
                    )
                )
                return
            e._convert_ids_types = True
            e._parent = self
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
                context_store[parentCtx] + "/" + nodePath + "/" + str(1)
            )
        self.resize(size)
        for i in range(size):
            context_store.update(
                aosCtx, context_store[parentCtx] + "/" + nodePath + "/" + str(i + 1)
            )  # Update context
            self.value[i].get(aosCtx, homogeneousTime)
            self._ull.ual_iterate_over_arraystruct(aosCtx, 1)

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
            context_store.update(
                aosCtx, context_store[parentCtx] + "/" + nodePath + "/" + str(i + 1)
            )  # Update context
            # This loops over the whole array
            dbg_str = " " * self.depth + "- [" + str(i + 1) + "]"
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

        status = self._ull.ual_end_action(aosCtx)
        context_store.pop(aosCtx)
        if status != 0:
            raise ALException(
                'ERROR: ual_end_action failed for "{!s}"'.format(self._name), status
            )