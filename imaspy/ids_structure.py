# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" A structure in an IDS

* :py:class:`IDSStructure`
"""
# Set up logging immediately

from imaspy.al_exception import ALException
from imaspy.ids_defs import DOUBLE_DATA, NODE_TYPE_STRUCTURE, READ_OP
from imaspy.ids_mixin import IDSMixin
from imaspy.ids_primitive import IDSPrimitive, create_leaf_container
from imaspy.logger import logger, loglevel


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
        for child in structure_xml:
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
                from imaspy.ids_struct_array import IDSStructArray

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
                from imaspy.ids_struct_array import create_leaf_container

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
            from imaspy.ids_struct_array import IDSStructArray

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
