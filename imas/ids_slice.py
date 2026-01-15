# This file is part of IMAS-Python.
# You should have received the IMAS-Python LICENSE file with this project.
"""IDSSlice represents a collection of IDS nodes matching a slice expression.

This module provides the IDSSlice class, which enables slicing of arrays of
structures while maintaining the hierarchy and allowing further operations on
the resulting collection.
"""

import logging
from typing import TYPE_CHECKING, Any, Iterator, List, Optional, Tuple, Union

import numpy as np

from imas.ids_metadata import IDSMetadata

if TYPE_CHECKING:
    from imas.ids_struct_array import IDSStructArray

logger = logging.getLogger(__name__)


class IDSSlice:
    """Represents a slice of IDS struct array elements.

    When slicing an IDSStructArray, instead of returning a regular Python list,
    an IDSSlice is returned. This allows for:
    - Tracking the slice operation in the path
    - Further slicing of child elements
    - Child node access on all matched elements
    - Iteration over matched elements

    Attributes:
        metadata: Metadata from the parent array (always present)
    """

    __slots__ = [
        "metadata",
        "_matched_elements",
        "_slice_path",
        "_parent_array",
        "_virtual_shape",
        "_element_hierarchy",
    ]

    def __init__(
        self,
        metadata: IDSMetadata,
        matched_elements: List[Any],
        full_path: str,
        parent_array: Optional["IDSStructArray"] = None,
        virtual_shape: Optional[Tuple[int, ...]] = None,
        element_hierarchy: Optional[List[Any]] = None,
    ):
        """Initialize IDSSlice.

        Args:
            metadata: Metadata from the parent array (required)
            matched_elements: List of elements that matched the slice
            full_path: Full path from the IDS root (e.g., "profiles_1d[:].ion[:]")
            parent_array: Optional reference to the parent IDSStructArray for context
            virtual_shape: Optional tuple representing multi-dimensional shape
            element_hierarchy: Optional tracking of element grouping
        """
        self.metadata = metadata
        self._matched_elements = matched_elements
        self._slice_path = full_path
        self._parent_array = parent_array
        self._virtual_shape = virtual_shape or (len(matched_elements),)
        self._element_hierarchy = element_hierarchy or [len(matched_elements)]

    @property
    def _path(self) -> str:
        """Return the path representation of this slice."""
        return self._slice_path

    @property
    def is_ragged(self) -> bool:
        """Check if the underlying data is ragged (non-rectangular).

        Ragged arrays have varying sizes at one or more dimensions.

        Returns:
            True if any dimension has varying sizes, False otherwise

        """
        # Check if any level in the hierarchy has non-uniform sizes
        for sizes_list in self._element_hierarchy:
            # sizes_list can be a list of sizes or a single integer
            if isinstance(sizes_list, list) and len(sizes_list) > 1:
                if len(set(sizes_list)) > 1:
                    return True
        return False

    @property
    def shape(self) -> Tuple[int, ...]:
        """Get the virtual multi-dimensional shape.

        Returns the shape of the data as if it were organized in a multi-dimensional
        array, based on the hierarchy of slicing operations performed.

        Raises:
            ValueError: The underlying data is ragged (non-rectangular).
                Use .is_ragged to check first, or use .values() to extract
                values as a flat list.

        Returns:
            Tuple of dimensions.
        """
        if self.is_ragged:
            raise ValueError(
                "Cannot get shape of ragged array: dimensions have varying "
                "sizes. Use .is_ragged to check if data is ragged, or .values() "
                "to get a flat list of elements."
            )

        # Build shape from hierarchy
        shape = []
        for i, hierarchy_level in enumerate(self._element_hierarchy):
            if isinstance(hierarchy_level, list):
                # This is a list of sizes
                if i == 0:
                    # First level with a list means grouped data
                    # The number of groups is the first hierarchy level (implicit)
                    shape.append(len(hierarchy_level))
                else:
                    # Subsequent levels: use first size (uniform, we checked is_ragged)
                    shape.append(hierarchy_level[0] if hierarchy_level else 0)
            else:
                # This is a single count
                shape.append(hierarchy_level)

        return tuple(shape)

    def __len__(self) -> int:
        """Return the number of elements matched by this slice."""
        return len(self._matched_elements)

    def __iter__(self) -> Iterator[Any]:
        """Iterate over all matched elements."""
        return iter(self._matched_elements)

    def __getitem__(self, item: Union[int, slice]) -> "IDSSlice":
        """Get element(s) from the slice using slice notation.

        Only slice operations are supported. Integer indexing on IDSSlice
        is not allowed to avoid confusion with array-wise operations.
        Use direct indexing on the IDS structure instead.

        Args:
            item: Slice object to apply

        Returns:
            IDSSlice: A new slice with the applied slice operation

        Raises:
            TypeError: If item is an integer (not supported)

        Examples:
            Slice operations (supported)::

                # Get ions 0 through 2 from all profiles
                result = cp.profiles_1d[:].ion[:3]  # OK - returns IDSSlice
                result = cp.profiles_1d[:].ion[1:3]  # OK - returns IDSSlice
                result = cp.profiles_1d[:].ion[::2]  # OK - returns IDSSlice

            Integer indexing (NOT supported)::

                # These will raise TypeError
                result = cp.profiles_1d[:].ion[0]  # ERROR!

            Recommended alternatives to integer indexing::

                # Option 1: Direct indexing (best - most efficient, clearest)
                result = cp.profiles_1d[0].ion[:]

                # Option 2: Convert slice to list first
                ions_list = list(cp.profiles_1d[:].ion)
                result = ions_list[0]

                # Option 3: Extract values
                ions_values = cp.profiles_1d[:].ion.values()
                result = ions_values[0]
        """
        if isinstance(item, slice):
            return self._handle_list_slice(item)
        else:
            # Integer indexing not allowed
            raise TypeError(
                f"Cannot index IDSSlice with integer {item}. "
                f"IDSSlice only supports slice notation (e.g., [0:5], [::2]).\n\n"
                f"To access elements, use one of these alternatives:\n"
                f"  1. Direct indexing (recommended):\n"
                f"     ids[{item}].node  # Access element directly\n"
                f"  2. Convert to list first:\n"
                f"     list(ids)[{item}]  # Convert slice to list\n"
                f"  3. Extract values:\n"
                f"     ids.values()[{item}]  # Get values as flat list"
            )

    def _handle_list_slice(self, item: slice) -> "IDSSlice":
        """Apply a slice operation to the matched elements list.

        Updates the first dimension of the shape to reflect the new
        number of elements after slicing.

        Args:
            item: The slice object to apply

        Returns:
            IDSSlice with updated shape and hierarchy
        """
        from imas.ids_struct_array import IDSStructArray

        slice_str = self._format_slice(item)
        # Full path: current path + slice operation
        full_path = self._path + slice_str

        # Check if matched elements are IDSStructArray (nested arrays)
        if self._matched_elements and isinstance(
            self._matched_elements[0], IDSStructArray
        ):
            # When slicing nested arrays, apply slice to each array and then flatten
            flattened_elements = []
            new_hierarchy_values = []
            for array in self._matched_elements:
                sliced_array = array[item]
                new_hierarchy_values.append(len(sliced_array))
                # Flatten: add each element from the sliced array to flattened list
                for element in sliced_array:
                    flattened_elements.append(element)

            # Build new hierarchy
            # The key is: if we have a multi-level grouped hierarchy
            # (like [3, [2, 2, 2], ...]), we're dealing with a nested
            # structure that's already been flattened. We should only update
            # the innermost level, NOT create a new top-level grouping.

            num_groups = len(self._matched_elements)

            if (
                len(self._element_hierarchy) >= 2
                and isinstance(self._element_hierarchy[0], int)
                and isinstance(self._element_hierarchy[1], list)
            ):
                # Multi-level hierarchy like [3, [2, 2, 2], ...]
                # The top level is the original grouping, so DON'T recreate it
                # Just replace the last (innermost) level
                new_hierarchy = self._element_hierarchy[:-1] + [new_hierarchy_values]
            else:
                # Single level or not grouped yet - create new grouping
                new_hierarchy = [num_groups, new_hierarchy_values]

            return IDSSlice(
                self.metadata,
                flattened_elements,
                full_path,
                parent_array=self._parent_array,
                virtual_shape=(len(flattened_elements),),
                element_hierarchy=new_hierarchy,
            )
        else:
            # Normal slice on outer list
            sliced_elements = self._matched_elements[item]

            # Update shape to reflect the slice on first dimension
            new_virtual_shape = (len(sliced_elements),) + self._virtual_shape[1:]
            new_element_hierarchy = [len(sliced_elements)] + self._element_hierarchy[1:]

            return IDSSlice(
                self.metadata,
                sliced_elements,
                full_path,
                parent_array=self._parent_array,
                virtual_shape=new_virtual_shape,
                element_hierarchy=new_element_hierarchy,
            )

    def __getattr__(self, name: str) -> "IDSSlice":
        """Access a child node on all matched elements.

        Returns a new IDSSlice containing the child node from each matched
        element. Validates the attribute name against metadata, allowing
        empty slices with valid child node names.

        Args:
            name: Name of the node to access

        Returns:
            A new IDSSlice containing the child node from each matched element,
            or an empty IDSSlice if the matched_elements is empty but the
            attribute name is valid according to metadata.

        Raises:
            AttributeError: If name is not a valid child node in the metadata
        """
        from imas.ids_struct_array import IDSStructArray
        from imas.ids_primitive import IDSNumericArray

        # Validate attribute name via metadata
        try:
            child_metadata = self.metadata[name]
        except (KeyError, TypeError):
            raise AttributeError(
                f"'{self.metadata.name}' has no child node '{name}'"
            ) from None

        # Full path: current path + attribute access
        full_path = self._path + "." + name

        # Handle empty slice - valid if metadata says it's a valid node
        if not self._matched_elements:
            return IDSSlice(
                child_metadata,
                [],
                full_path,
                parent_array=self._parent_array,
                virtual_shape=(0,),
                element_hierarchy=[0],
            )

        # Get attributes from all non-empty matched elements
        # Special case: if matched_elements are IDSStructArray, keep them grouped
        if self._matched_elements and isinstance(
            self._matched_elements[0], IDSStructArray
        ):
            # For nested arrays, return the arrays themselves, not attributes from them
            # This allows chaining like .ion[:].element[:] to work
            child_elements = self._matched_elements
        else:
            child_elements = [getattr(element, name) for element in self]

        # Check if children are IDSStructArray (nested arrays) or IDSNumericArray
        if not child_elements:
            # Empty child elements
            return IDSSlice(
                child_metadata,
                child_elements,
                full_path,
                parent_array=self._parent_array,
                virtual_shape=self._virtual_shape,
                element_hierarchy=self._element_hierarchy,
            )

        # If matched_elements are IDSStructArray and we're accessing an
        # attribute on them, we need to get that attribute from each
        # array's elements
        if isinstance(self._matched_elements[0], IDSStructArray):
            # Accessing attribute on nested arrays: get attr from each
            # array's elements
            flattened_elements = []
            for array in child_elements:
                # array is IDSStructArray, get attribute from its elements
                for element in array:
                    flattened_elements.append(getattr(element, name))

            # Keep track of grouping for shape preservation
            child_sizes = [len(array) for array in child_elements]

            return IDSSlice(
                child_metadata,
                flattened_elements,
                full_path,
                parent_array=self._parent_array,
                virtual_shape=self._virtual_shape + (None,),
                element_hierarchy=self._element_hierarchy + [child_sizes],
            )

        if isinstance(child_elements[0], IDSStructArray):
            # Children are IDSStructArray - track the new dimension
            child_sizes = [len(arr) for arr in child_elements]

            # New virtual shape: current shape + new dimension
            # Store actual sizes (may be ragged) - don't assume all are the same!
            new_virtual_shape = self._virtual_shape + (None,)
            new_hierarchy = self._element_hierarchy + [child_sizes]

            return IDSSlice(
                child_metadata,
                child_elements,
                full_path,
                parent_array=self._parent_array,
                virtual_shape=new_virtual_shape,
                element_hierarchy=new_hierarchy,
            )
        elif isinstance(child_elements[0], IDSNumericArray):
            # Children are IDSNumericArray - track the array dimension
            # Each IDSNumericArray has a size (length of its data)
            child_sizes = [len(arr) for arr in child_elements]

            # New virtual shape: current shape + new dimension
            # Store actual sizes (may be ragged) - don't assume all are the same!
            new_virtual_shape = self._virtual_shape + (None,)
            new_hierarchy = self._element_hierarchy + [child_sizes]

            return IDSSlice(
                child_metadata,
                child_elements,
                full_path,
                parent_array=self._parent_array,
                virtual_shape=new_virtual_shape,
                element_hierarchy=new_hierarchy,
            )
        else:
            # Children are not arrays (structures or other primitives)
            return IDSSlice(
                child_metadata,
                child_elements,
                full_path,
                parent_array=self._parent_array,
                virtual_shape=self._virtual_shape,
                element_hierarchy=self._element_hierarchy,
            )

    def __repr__(self) -> str:
        """Build a string representation of this IDSSlice.

        Returns a string showing:
        - The IDS type name (e.g., 'equilibrium')
        - The full path including slice operations (e.g., 'profiles_1d[:].ion[:]')
        - The number of matched elements

        Returns:
            String representation like:
            '<IDSSlice (IDS:core_profiles, profiles_1d[:].ion[:] with 318 items)>'
        """
        ids_name = self.metadata.ids_name
        item_word = "item" if len(self) == 1 else "items"
        return (
            f"<{type(self).__name__} (IDS:{ids_name}, {self._path} with "
            f"{len(self)} {item_word})>"
        )

    def values(self) -> List[Any]:
        """Extract raw values from elements in this slice.

        For IDSPrimitive elements, this extracts the wrapped value.
        For other element types, returns them as-is.

        Returns a flat list of extracted values. This is useful for getting
        the actual data without the IDS wrapper when accessing scalar fields
        through a slice, without requiring explicit looping through the
        original collection.

        For multi-dimensional access to values, use one of these approaches:

        - Use direct indexing: ``ids_obj[i1].collection[i2].value`` (best
          performance and clarity)
        - Use ``.to_array()`` if you need numpy array integration

        Returns:
            List of raw Python/numpy values or unwrapped elements

        Examples:
            Extract scalar values from a 1D slice::

                # Get list of temperatures from all profiles
                temps = core_profiles.profiles_1d[:].te.values()

            For multi-dimensional access, use direct indexing instead::

                # Get a specific temperature (more efficient than slicing)
                temp = core_profiles.profiles_1d[0].te.values()[5]

                # Or better yet, direct access
                temp_value = core_profiles.profiles_1d[0].te[5]

            For converting to numpy arrays::

                # Use to_array() for tensorization
                array = core_profiles.profiles_1d[:].te.to_array()
        """
        from imas.ids_primitive import IDSPrimitive

        result = []
        for element in self._matched_elements:
            if isinstance(element, IDSPrimitive):
                result.append(element.value)
            else:
                result.append(element)
        return result

    def to_array(self) -> np.ndarray:
        """Convert this slice to a numpy array - for leaf node slices only.

        This method converts a slice containing scalar or numeric array leaf nodes
        to a regular numpy array with shape self.shape. It is designed for
        tensorization of leaf nodes only (e.g., slices of FLT_1D, profiles, etc.).

        For multi-dimensional access to non-leaf nodes, use direct indexing instead:
        ``ids[i1][i2]`` rather than slicing with ``.to_array()``.

        Returns:
            numpy.ndarray with shape self.shape containing the extracted values.

        Raises:
            ValueError: If slice refers to IDSStructure or IDSStructArray elements
                (non-leaf nodes). Use direct indexing instead.
            ValueError: If the data is ragged/non-rectangular (dimensions have
                varying sizes). Use direct indexing or ``.values()`` instead.
            ValueError: If values cannot be converted to numpy array.

        Examples:
            Tensorize a 1D slice of numeric data::

                # Works: leaf nodes are numeric arrays
                array = core_profiles.profiles_1d[:].te.to_array()
                # Shape: (n_profiles,)

            Multi-dimensional tensorization::

                # Works: accessing leaf nodes from nested structure
                array = core_profiles.profiles_1d[:].te.to_array()
                # Shape: (n_profiles,)

            Direct indexing for non-leaf nodes::

                # Don't do this - will raise ValueError
                # array = core_profiles.profiles_1d[:].to_array()  # ERROR!

                # Do this instead
                profile = core_profiles.profiles_1d[0]  # Direct access
                te = profile.te.to_array()  # Then tensorize
        """
        from imas.ids_primitive import IDSPrimitive, IDSNumericArray
        from imas.ids_struct_array import IDSStructArray
        from imas.ids_structure import IDSStructure

        # Validate: slice must refer to leaf nodes only
        if self._matched_elements:
            first = self._matched_elements[0]
            if isinstance(first, (IDSStructure, IDSStructArray)):
                raise ValueError(
                    f"Cannot tensorize {type(first).__name__} slice - only "
                    f"works for leaf nodes (scalars, numeric arrays). Use "
                    f"direct indexing instead: ids[i][j] to access structures."
                )

        # Validate: data must be rectangular (not ragged)
        if self.is_ragged:
            raise ValueError(
                "Cannot tensorize ragged array - dimensions have varying "
                "sizes. Use .values() to get a flat list, or use direct "
                "indexing for multi-dimensional access."
            )

        # Get the target shape (we validated it's not ragged)
        actual_shape = self.shape

        # Handle empty slice
        if len(self._matched_elements) == 0:
            return np.empty(actual_shape, dtype=float)

        # Extract values from leaf nodes
        flat_values = []
        for element in self._matched_elements:
            if isinstance(element, IDSPrimitive):
                flat_values.append(element.value)
            elif isinstance(element, IDSNumericArray):
                flat_values.append(element.value)
            else:
                flat_values.append(element)

        # Tensorize to target shape
        arr = np.array(flat_values)

        # For 1D, no reshape needed
        if len(actual_shape) == 1:
            return arr

        # For multi-dimensional, reshape to target shape
        try:
            return arr.reshape(actual_shape)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Failed to convert slice to array with shape {actual_shape}: {e}"
            )

    @staticmethod
    def _format_slice(slice_obj: slice) -> str:
        """Format a slice object as a string.

        Args:
            slice_obj: The slice object to format

        Returns:
            String representation like "[1:5]", "[::2]", etc.
        """
        start = slice_obj.start if slice_obj.start is not None else ""
        stop = slice_obj.stop if slice_obj.stop is not None else ""
        step = slice_obj.step if slice_obj.step is not None else ""

        if step:
            return f"[{start}:{stop}:{step}]"
        else:
            return f"[{start}:{stop}]"
