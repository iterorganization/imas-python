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
            ValueError: The underlying data is ragged (non-rectangular). Use 
                .is_ragged to check first, or use
                .to_array() to convert to a numpy object array.

        Returns:
            Tuple of dimensions.
        """
        if self.is_ragged:
            raise ValueError(
                f"Cannot get shape of ragged array: dimensions have varying sizes. "
                f"Use .is_ragged to check if data is ragged, or .to_array() to "
                f"convert to numpy object array."
            )
        
        # Build shape from hierarchy, replacing None with actual uniform size
        shape = []
        for hierarchy_level in self._element_hierarchy:
            if isinstance(hierarchy_level, list):
                # This is a list of sizes - get the uniform size (we checked is_ragged)
                shape.append(hierarchy_level[0])
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
        """Get element(s) from the slice.

        When the matched elements are IDSStructArray objects, the indexing
        operation is applied to each array element (array-wise indexing).
        Otherwise, the operation is applied to the matched elements list itself.

        Args:
            item: Index or slice to apply

        Returns:
            - IDSSlice: If item is a slice, or if applying integer index to
              IDSStructArray elements
            - Single element: If item is an int and elements are not IDSStructArray
        """
        from imas.ids_struct_array import IDSStructArray

        # Check if we have array-wise indexing (elements are IDSStructArray)
        if self._matched_elements and isinstance(
            self._matched_elements[0], IDSStructArray
        ):
            if isinstance(item, slice):
                return self._handle_array_wise_slice(item)
            else:
                return self._handle_array_wise_integer(item)
        else:
            if isinstance(item, slice):
                return self._handle_list_slice(item)
            else:
                return self._matched_elements[int(item)]

    def _handle_array_wise_slice(self, item: slice) -> "IDSSlice":
        """Apply a slice operation array-wise to IDSStructArray elements.

        Applies the slice to each array element and preserves the grouping
        structure for multi-dimensional shapes.

        Args:
            item: The slice object to apply

        Returns:
            IDSSlice with updated shape and hierarchy
        """
        sliced_elements = []
        sliced_sizes = []

        for array in self._matched_elements:
            sliced = array[item]
            if isinstance(sliced, IDSSlice):
                sliced_elements.extend(sliced._matched_elements)
                sliced_sizes.append(len(sliced))
            else:
                sliced_elements.append(sliced)
                sliced_sizes.append(1)

        slice_str = self._format_slice(item)
        # Full path: current path + slice operation
        full_path = self._path + slice_str

        # Update shape to reflect the sliced structure
        # Keep first dimensions, store actual sizes (may be ragged)
        new_virtual_shape = self._virtual_shape[:-1] + (None,)
        new_hierarchy = self._element_hierarchy[:-1] + [sliced_sizes]

        return IDSSlice(
            self.metadata,
            sliced_elements,
            full_path,
            parent_array=self._parent_array,
            virtual_shape=new_virtual_shape,
            element_hierarchy=new_hierarchy,
        )

    def _handle_array_wise_integer(self, item: int) -> "IDSSlice":
        """Apply integer indexing array-wise to IDSStructArray elements.

        Applies the integer index to each array element, reducing the last
        dimension to size 1.

        Args:
            item: The integer index to apply

        Returns:
            IDSSlice with updated shape
        """
        indexed_elements = [array[int(item)] for array in self._matched_elements]

        # Full path: current path + index operation
        full_path = self._path + f"[{item}]"

        # Shape changes: last dimension becomes 1
        new_virtual_shape = self._virtual_shape[:-1] + (1,)

        return IDSSlice(
            self.metadata,
            indexed_elements,
            full_path,
            parent_array=self._parent_array,
            virtual_shape=new_virtual_shape,
            element_hierarchy=self._element_hierarchy,
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
        sliced_elements = self._matched_elements[item]
        slice_str = self._format_slice(item)
        # Full path: current path + slice operation
        full_path = self._path + slice_str

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
        return f"<{type(self).__name__} (IDS:{ids_name}, {self._path} with {len(self)} {item_word})>"

    def values(self) -> List[Any]:
        """Extract raw values from elements in this slice.

        For IDSPrimitive elements, this extracts the wrapped value.
        For other element types, returns them as-is.

        Returns a flat list of extracted values. This is useful for getting 
        the actual data without the IDS wrapper when accessing scalar fields 
        through a slice, without requiring explicit looping through the 
        original collection.

        For multi-dimensional access to values:
        - Use direct indexing: ``ids_obj[i1].collection[i2].value`` for best 
          performance and clarity
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
        """Convert this slice to a numpy array respecting multi-dimensional structure.

        For 1D slices: returns a simple 1D array.
        For multi-dimensional slices: returns an array with shape self.shape.
        For ragged data: returns an object array containing the elements as-is.

        This is useful for integration with numpy operations, scipy functions,
        and xarray data structures. The returned array preserves the hierarchical
        structure of the IMAS data.

        Returns:
            numpy.ndarray with shape self.shape, or object array if ragged.

        Raises:
            ValueError: If array cannot be converted to numpy
        """
        from imas.ids_primitive import IDSPrimitive, IDSNumericArray

        # Try to get the actual shape (will check if ragged)
        try:
            actual_shape = self.shape  # Will raise if ragged
            is_ragged_data = False
        except ValueError:
            # Data is ragged - handle it gracefully
            is_ragged_data = True
            actual_shape = None

        # 1D case - simple conversion
        if not is_ragged_data and len(actual_shape) == 1:
            flat_values = []
            for element in self._matched_elements:
                if isinstance(element, IDSPrimitive):
                    flat_values.append(element.value)
                else:
                    flat_values.append(element)
            try:
                return np.array(flat_values)
            except (ValueError, TypeError):
                return np.array(flat_values, dtype=object)

        # Multi-dimensional case
        # Check if matched elements are themselves arrays (IDSNumericArray)
        if self._matched_elements and isinstance(
            self._matched_elements[0], IDSNumericArray
        ):
            # Elements are numeric arrays - extract their values and stack them
            array_values = []
            for element in self._matched_elements:
                if isinstance(element, IDSNumericArray):
                    array_values.append(element.value)
                else:
                    array_values.append(element)

            # For ragged data, return object array with arrays as elements
            if is_ragged_data:
                return np.array(array_values, dtype=object)

            # Try to stack into proper shape
            try:
                # Check if all arrays have the same size (regular)
                sizes = []
                for val in array_values:
                    if hasattr(val, "__len__"):
                        sizes.append(len(val))
                    else:
                        sizes.append(1)

                # If all sizes are the same, we can create a regular array
                if len(set(sizes)) == 1:
                    # Regular array - all sub-arrays same size
                    stacked = np.array(array_values)
                    # Should now have shape (first_dim, second_dim)
                    if stacked.shape == actual_shape:
                        return stacked
                    else:
                        # Try explicit reshape
                        try:
                            return stacked.reshape(actual_shape)
                        except ValueError:
                            # If reshape fails, return as object array
                            result_arr = np.empty(actual_shape, dtype=object)
                            for i, val in enumerate(array_values):
                                result_arr.flat[i] = val
                            return result_arr
                else:
                    result_arr = np.empty(actual_shape[0], dtype=object)
                    for i, val in enumerate(array_values):
                        result_arr[i] = val
                    return result_arr
            except (ValueError, TypeError):
                # Fallback: return object array
                result_arr = np.empty(actual_shape[0], dtype=object)
                for i, val in enumerate(array_values):
                    result_arr[i] = val
                return result_arr

        # For non-numeric elements in multi-dimensional structure
        # Extract and try to build structure
        flat_values = []

        # First check if matched_elements are IDSStructArray (which need flattening)
        from imas.ids_struct_array import IDSStructArray

        has_struct_arrays = self._matched_elements and isinstance(
            self._matched_elements[0], IDSStructArray
        )

        if has_struct_arrays:
            # Flatten IDSStructArray elements
            for struct_array in self._matched_elements:
                for element in struct_array:
                    if isinstance(element, IDSPrimitive):
                        flat_values.append(element.value)
                    else:
                        flat_values.append(element)
        else:
            # Regular elements
            for element in self._matched_elements:
                if isinstance(element, IDSPrimitive):
                    flat_values.append(element.value)
                else:
                    flat_values.append(element)

        # For ragged data, construct object array from hierarchy
        if is_ragged_data:
            # Build object array respecting the ragged structure
            if len(self._element_hierarchy) == 1:
                # Simple 1D array
                return np.array(flat_values, dtype=object)
            else:
                # Multi-level hierarchy - reconstruct structure
                result_arr = np.empty(self._element_hierarchy[0], dtype=object)
                idx = 0
                for i in range(self._element_hierarchy[0]):
                    group_size = self._element_hierarchy[1][i]
                    result_arr[i] = flat_values[idx:idx+group_size]
                    idx += group_size
                return result_arr

        total_size = 1
        for dim in actual_shape:
            total_size *= dim

        # Check if we have the right number of elements
        if len(flat_values) != total_size:
            raise ValueError(
                f"Cannot convert to array: expected {total_size} elements "
                f"but got {len(flat_values)}"
            )

        # Try to create the array
        try:
            arr = np.array(flat_values)
            try:
                # Try to reshape to target shape
                return arr.reshape(actual_shape)
            except (ValueError, TypeError):
                # If reshape fails, use object array
                arr_obj = np.empty(actual_shape, dtype=object)
                for i, val in enumerate(flat_values):
                    arr_obj.flat[i] = val
                return arr_obj
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to convert slice to numpy array: {e}")

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
