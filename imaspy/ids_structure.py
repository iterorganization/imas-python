# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" A structure in an IDS

* :py:class:`IDSStructure`
"""

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

import logging
from distutils.version import StrictVersion as V

from imaspy.setup_logging import root_logger as logger
from imaspy.al_exception import ALException
from imaspy.ids_mixin import IDSMixin, get_coordinates
from imaspy.ids_primitive import IDSPrimitive, create_leaf_container

try:
    from imaspy.ids_defs import DOUBLE_DATA, NODE_TYPE_STRUCTURE, READ_OP
except ImportError:
    logger.critical("IMAS could not be imported. UAL not available!")


class IDSStructure(IDSMixin):
    """IDS structure node

    Represents a node in the IDS tree. Does not itself contain data,
    but contains references to leaf nodes with data (IDSPrimitive) or
    other node-like structures, for example other IDSStructures or
    IDSStructArrays
    """

    _MAX_OCCURRENCES = None
    _convert_ids_types = False

    def getNodeType(self):
        raise NotImplementedError("{!s}.getNodeType()".format(self))
        return NODE_TYPE_STRUCTURE

    # def __deepcopy__(self, memo):
    #    raise NotImplementedError

    # def __copy__(self):
    #    raise NotImplementedError
    def __init__(self, parent, name, structure_xml):
        """Initialize IDSStructure from XML specification

        Initializes in-memory an IDSStructure. The XML should contain
        all direct descendants of the node. To avoid duplication,
        none of the XML structure is saved directly, so this transformation
        might be irreversible.

        Args:
            parent: Parent structure. Can be anything, but at database write
                time should be something with a path attribute
            name: Name of the node itself. Will be used in path generation when
                stored in DB
            structure_xml: Object describing the structure of the IDS. Usually
                an instance of `xml.etree.ElementTree.Element`
        """
        # To ease setting values at this stage, do not try to cast values
        # to canonical forms
        # Since __setattr__ looks for _convert_ids_types we set it through __dict__
        self.__dict__["_convert_ids_types"] = False
        super().__init__(parent, name, structure_xml=structure_xml)

        self._base_path = name
        self._children = []  # Store the children as a list of strings.
        # Loop over the direct descendants of the current node.
        # Do not loop over grandchildren, that is handled by recursiveness.

        self._is_slice = False

        if logger.level <= logging.DEBUG:
            log_string = " " * self.depth + " - % -38s initialization"

        for child in structure_xml:
            my_name = child.get("name")
            if logger.level <= logging.TRACE:
                logger.trace(log_string, my_name)
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
                    pass
                    # logger.critical(
                    # "Found a timebasepath of {!s}! Should not happen".format(tbp)
                    # )
                coordinates = get_coordinates(child)
                setattr(
                    self,
                    my_name,
                    create_leaf_container(
                        my_name,
                        my_data_type,
                        parent=self,
                        coordinates=coordinates,
                        var_type=child.get("type"),
                    ),
                )
        # After initialization, always try to convert setting attributes on this structure
        self._convert_ids_types = True

    @property
    def has_value(self):
        """True if any of the children has a non-default value"""
        return any(map(lambda el: el.has_value, self))

    def keys(self):
        """Behave like a dictionary by defining a keys() method"""
        return self._children

    def values(self):
        """Behave like a dictionary by defining a values() method"""
        return map(self.__getitem__, self._children)

    def items(self):
        """Behave like a dictionary by defining an items() method"""
        # define values inline, because some IDSes overwrite values
        return zip(self.keys(), map(self.__getitem__, self._children))

    def set_backend_properties(self, structure_xml):
        """Loop over a structure's backend properties and those of its children"""
        # set my own properties
        up, skip = super().set_backend_properties(structure_xml)
        # skip if structure_xml was already seen
        if skip:
            return

        # recurse to my children
        for child_name in self._children:
            child = self[child_name]
            # Decide whether we should look for an element with a different name
            # or the same one. when migrating up the current in_memory xml
            # contains information about migrations.
            xml_child = None
            no_backend_structure_xml_found = False
            if up:
                cur_mem_child_xml = self._structure_xml.find(
                    "field[@name='{name}']".format(name=child_name)
                )
                if "change_nbc_previous_name" in cur_mem_child_xml.attrib:
                    # if the version at which the change happened is > the backend
                    # and <= our version we need to take it into account
                    if (
                        V(self.backend_version)
                        < V(cur_mem_child_xml.attrib["change_nbc_version"])
                        <= V(self._version)
                    ):
                        # change_nbc_previous_name can contain paths.
                        # the access layer takes care of proper reading for us
                        # (since we just concatenate names to form paths)
                        child_name = cur_mem_child_xml.attrib[
                            "change_nbc_previous_name"
                        ]
                        logger.info(
                            "Mapping field %s.%s->%s",
                            self._name,
                            child._name,
                            child_name,
                        )
                        # in principle this doesn't have to mean that we have
                        # the right element but in most cases it will.
                        # it would not, for instance, if between two versions
                        # an element is renamed and a different, new element
                        #  takes its place. We will cross that bridge when we get to it.
            else:
                # the memory version is older, so the migration information
                # will be in the backend. We must first search for a field
                # which could have been renamed to the current one, and after
                # that check the current name.
                xml_child = structure_xml.find(
                    "field[@change_nbc_previous_name='{name}']".format(name=child._name)
                )
                # the renamed field can actually be a path instead of a name
                # in which case we have the following situation
                # old:
                #   |-a
                #     |- b
                # new
                #  |- c
                #
                # and c has change_nbc_previous_name='a/b'.
                # in this branch (down, i.e. memory is old and file is new)
                # we are now at b, and therefore
                # need to look in the structure_xml of parent for change_nbc_previous_name
                # of 'a/b' to match the elements
                # (actually we should probably do it recursively, but let's
                # support only one level for now)
                if xml_child is None and isinstance(self._parent, IDSStructure):
                    # we are really looking for a sibling of ourselves, so
                    # we look in the parents children
                    try:
                        xml_child = self._parent._backend_structure_xml.find(
                            "field[@change_nbc_previous_name='{pname}/{name}']".format(
                                pname=self._name, name=child._name
                            )
                        )
                    except AttributeError:
                        # probably does not exist since we are calling this
                        # at creation time of a child of a structarray.
                        # this is really only a problem if the 'normal' child
                        # is not found.
                        # setup a flag preparing a warning then.
                        no_backend_structure_xml_found = True

                # qualify the found xml_child to see if it was renamed within
                # our version range
                if xml_child:
                    if (
                        not V(self._version)
                        < V(xml_child.attrib["change_nbc_version"])
                        <= V(self.backend_version)
                    ):
                        xml_child = None
                    else:
                        logger.info(
                            "Mapping field %s.%s->%s",
                            self._name,
                            child._name,
                            xml_child.attrib["name"],
                        )

            # if the above 2 procedures did not find the child try a direct name search
            if xml_child is None:
                xml_child = structure_xml.find(
                    "field[@name='{name}']".format(name=child_name)
                )

            if xml_child is None:
                # if the xml_child was not found make some noise
                if up:
                    logger.warning(
                        "No matching child %s found for %s.%s.",
                        child_name,
                        self._name,
                        child._name,
                    )
                else:
                    if no_backend_structure_xml_found:
                        logger.warning(
                            "Rename not supported for delayed construction of %s.%s",
                            self._name,
                            child._name,
                        )
                    logger.warning(
                        "Tried to find renamed field %s for %s.%s but failed, skipping.",
                        child_name,
                        self._name,
                        child._name,
                    )

            else:
                child.set_backend_properties(xml_child)

        # all of my children are initialized, and we can delete
        # the temporarily stored _backend_structure_xml for them
        for child in self:
            try:
                del child._backend_structure_xml
            except AttributeError:
                pass

    def __iter__(self):
        """Iterate over this structure's children"""
        return iter(map(self.__getitem__, self._children))

    @cached_property
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
        if self._convert_ids_types and not key[0] == "_":
            # Convert IDS type on set time. Never try this for hidden attributes!
            if hasattr(self, key):
                attr = getattr(self, key)
            else:
                # Structure does not exist. It should have been pre-generated
                raise NotImplementedError(
                    "generating new structure from scratch {name}".format(name=key)
                )

                # attr = create_leaf_container(key, no_data_type_I_guess, parent=self)
            if isinstance(attr, IDSStructure) and not isinstance(value, IDSStructure):
                raise Exception(
                    "Trying to set structure field {!s} with non-structure.".format(key)
                )

            attr.value = value
            # super().__setattr__(key, attr)
        else:
            super().__setattr__(key, value)

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

    def get(self, ctx, homogeneousTime):
        """Get data from UAL backend storage format and overwrite data in node

        Tries to dynamically build all needed information for the UAL.
        """
        if len(self._children) == 0:
            logger.warning('Trying to get structure "%s" with 0 children', self._name)
        if logger.level <= logging.DEBUG:
            log_string = " " * self.depth + " - % -38s get"
        for child_name in self._children:
            if logger.level <= logging.DEBUG:
                logger.debug(log_string, child_name)
            child = getattr(self, child_name)
            if isinstance(child, IDSStructure):
                child.get(ctx, homogeneousTime)
                continue  # Nested struct will handle setting attributes
            if isinstance(child, IDSPrimitive):
                status, data = child.get(ctx, homogeneousTime)
            else:
                logger.critical(
                    "Unknown type %s for field %s! Skipping", type(child), child_name
                )
            if status == 0 and data is not None:
                setattr(self, child_name, data)
            elif status != 0:
                logger.critical(
                    "Unable to get simple field %s, UAL return code %s",
                    child_name,
                    status,
                )
            else:
                logger.debug("Unable to get simple field %s, seems empty", child_name)

    def _getData(self, ctx, homogeneousTime, nodePath, analyzeTime):
        """ A deeped way of getting data?? using 'traverser' whatever that is """
        raise NotImplementedError(
            "{!s}._getData(ctx, homogeneousTime, nodePath, analyzeTime)".format(self)
        )

    def put(self, ctx, homogeneousTime, **kwargs):
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
            if logger.level <= logging.DEBUG:
                log_string = " " * self.depth + " - % -38s put"
            if child is not None:
                if not isinstance(child, IDSPrimitive):
                    if logger.level <= logging.DEBUG:
                        logger.debug(log_string, child_name)
                child.put(ctx, homogeneousTime, **kwargs)

    def setPulseCtx(self, ctx):
        raise DeprecationWarning(
            "IDSs should not set context directly, set on Root node instead"
        )

    def getPulseCtx(self):
        raise DeprecationWarning(
            "IDSs should not set context directly, set on Root node instead"
        )

    def delete(self, ctx):
        """Delete data from UAL backend storage"""
        for child_name in self._children:
            child = getattr(self, child_name)
            if logger.level <= logging.DEBUG:
                log_string = " " * self.depth + " - % -38s del"
                logger.debug(log_string, child_name)
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
