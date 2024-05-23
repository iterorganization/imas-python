# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""NetCDF IO support for IMASPy. Requires [netcdf] extra dependencies.
"""

from collections.abc import Container
from typing import Iterator, Tuple

import netCDF4
import numpy

from imaspy.ids_base import IDSBase
from imaspy.ids_data_type import IDSDataType
from imaspy.ids_metadata import IDSMetadata
from imaspy.ids_struct_array import IDSStructArray
from imaspy.ids_structure import IDSStructure
from imaspy.ids_toplevel import IDSToplevel
from imaspy.netcdf.nc_metadata import NCMetadata

default_fillvals = {
    IDSDataType.INT: netCDF4.default_fillvals["i4"],
    IDSDataType.STR: "",
    IDSDataType.FLT: netCDF4.default_fillvals["f8"],
    IDSDataType.CPX: netCDF4.default_fillvals["f8"] * (1 + 1j),
}


def filter_coordinates(coordinates: str, filled_variables: Container):
    return " ".join(
        coordinate
        for coordinate in coordinates.split(" ")
        if coordinate in filled_variables
    )


def create_variable(
    group: netCDF4.Group,
    metadata: IDSMetadata,
    ncmeta: NCMetadata,
    homogeneous_time: bool,
) -> netCDF4.Variable:
    """Create a new variable for the quantity described by metadata.

    Args:
        group: netCDF4 group to create the variable in.
        metadata: IDSMetadata describing the variable.
        ncmeta: NetCDF metadata for the IDS.
        homogeneous_time: True iff the IDS uses homogeneous time coordinates.

    Returns:
        The created variable.
    """
    path = metadata.path_string
    var_name = path.replace("/", ".")

    if metadata.data_type in (IDSDataType.STRUCTURE, IDSDataType.STRUCT_ARRAY):
        # Create a 0D dummy variable for the metadata
        var = group.createVariable(var_name, "S1", ())

    else:
        # Determine datatype
        dtype = metadata.data_type.numpy_dtype
        if dtype is None and metadata.data_type == IDSDataType.STR:
            dtype = str
        assert dtype is not None

        # Create variable
        var = group.createVariable(
            var_name,
            dtype,
            ncmeta.get_dimensions(path, homogeneous_time),
            compression=None if dtype is str else "zlib",
            complevel=1,
            fill_value=default_fillvals[metadata.data_type],
        )

    # Fill common attributes:
    var.documentation = metadata.documentation
    if metadata.units:
        var.units = metadata.units

    return var


def nc_tree_iter(
    node: IDSStructure, aos_index: Tuple[int, ...] = ()
) -> Iterator[Tuple[Tuple[int, ...], IDSBase]]:
    """Tree iterator that tracks indices of all ancestor array of structures.

    Args:
        node: IDS node to iterate over

    Yields:
        (aos_index, node) for all filled leaf nodes and array of structures nodes.
    """
    for child in node.iter_nonempty_():
        yield (aos_index, child)
        if isinstance(child, IDSStructArray):
            for i in range(len(child)):
                yield from nc_tree_iter(child[i], aos_index + (i,))
        elif isinstance(child, IDSStructure):
            yield from nc_tree_iter(child, aos_index)


def ids2nc(ids: IDSToplevel, group: netCDF4.Group):
    """Store IDS using IMAS conventions in the provided group.

    Args:
        ids: IDS to store
        group: Empty netCDF4 Group
    """
    # Get NCMetadata for this IDS
    # TODO: cache this?
    ncmeta = NCMetadata(ids.metadata)

    # Keep track of used dimensions, and the maximum size
    dimension_size = {}  # dim_name: size
    # Keep track of filled data per path
    filled_data = {path: {} for path in ncmeta.paths}  # path: {aos_indices: node}
    # homogeneous_time boolean
    homogeneous_time = ids.ids_properties.homogeneous_time == 1

    # Loop over the IDS to calculate the dimensions sizes
    for aos_index, node in nc_tree_iter(ids):
        dimensions = ncmeta.get_dimensions(node.metadata.path_string, homogeneous_time)
        ndim = node.metadata.ndim
        if ndim:
            for dim_name, size in zip(dimensions[-ndim:], node.shape):
                dimension_size[dim_name] = max(dimension_size.get(dim_name, 0), size)
        filled_data[node.metadata.path_string][aos_index] = node
    # Remove entries without data:
    filled_data = {path: data for path, data in filled_data.items() if data}
    filled_variables = {path.replace("/", ".") for path in filled_data}

    # Create NC dimensions
    for dimension, size in dimension_size.items():
        group.createDimension(dimension, size)
    # Generic ND dimensions for use in `shape` variables, don't create yet
    nd_dimensions = {}  # i: Dimension

    path_shapes = {}

    # Loop over the IDS another time to create variables and determine sparsity
    for path in filled_data:
        metadata = ids.metadata[path]
        var = create_variable(group, metadata, ncmeta, homogeneous_time)

        # We don't store (sparsity) data for structures
        if metadata.data_type is IDSDataType.STRUCTURE:
            continue

        # Determine if we need to store shapes (applicable for data variables and AOS)
        data = filled_data[path]
        ndim = metadata.ndim
        aos_dims = ()
        if path in ncmeta.aos:
            aos_dims = ncmeta.get_dimensions(ncmeta.aos[path], homogeneous_time)

        if len(aos_dims) == 0:
            # Data is not tensorized
            node = filled_data[path][()]
            sparse = node.shape != var.shape
            if sparse:
                shapes = numpy.array(node.shape, dtype=numpy.int32)

        else:
            # Data is tensorized, determine if it is homogeneously shaped
            shapes_shape = [dimension_size[dim] for dim in aos_dims]
            if ndim:
                shapes_shape.append(ndim)
            # Note: Access Layer API also allows maximum int32 to describe sizes
            # TODO: allow more efficient storage when sizes fit in int8 or int16?
            shapes = numpy.zeros(shapes_shape, dtype=numpy.int32)

            if ndim:
                for aos_coords, node in data.items():
                    shapes[aos_coords] = node.shape
                full_shape = [
                    dimension_size[dim]
                    for dim in ncmeta.get_dimensions(path, homogeneous_time)[-ndim:]
                ]
                sparse = not numpy.array_equiv(shapes, full_shape)

            else:  # 0D variables don't have a shape:
                for aos_coords in data.keys():
                    shapes[aos_coords] = 1
                sparse = not shapes.all()

        # Store sparsity metadata
        if sparse and ndim:
            # Store shape array
            if ndim not in nd_dimensions:
                nd_dimensions[ndim] = group.createDimension(f"{ndim}D", ndim)
            shape_var = group.createVariable(
                path.replace("/", ".") + ":shape",
                shapes.dtype,
                aos_dims + (nd_dimensions[ndim],),
                # compression="zlib",
                # complevel=1,
            )
            path_shapes[path] = shapes
            var.sparse = f"Sparse data, data shapes are stored in {shape_var.name}"
        elif sparse:
            var.sparse = "Sparse data, missing data is filled with _FillValue"

        # We don't store data for arrays of structures
        if metadata.data_type is IDSDataType.STRUCT_ARRAY:
            continue

        # Store coordinate metadata
        coordinates = ncmeta.get_coordinates(path, homogeneous_time)
        if coordinates:
            var.coordinates = filter_coordinates(coordinates, filled_variables)

    # Ensure variables and metadata are synchronized with HDF5 file
    group.sync()

    # Loop over the IDS another time to store the data
    for path in filled_data:
        metadata = ids.metadata[path]

        # We don't store (sparsity) data for structures
        if metadata.data_type is IDSDataType.STRUCTURE:
            continue

        if path in path_shapes:
            # Store sparse shape:
            shape_var = group[path.replace("/", ".") + ":shape"]
            shape_var[()] = path_shapes.pop(path)

        # We don't store data for arrays of structures
        if metadata.data_type is IDSDataType.STRUCT_ARRAY:
            continue

        var = group[path.replace("/", ".")]
        data = filled_data[path]
        ndim = metadata.ndim
        aos_dims = ()
        if path in ncmeta.aos:
            aos_dims = ncmeta.get_dimensions(ncmeta.aos[path], homogeneous_time)

        # Fill variable
        if len(aos_dims) == 0:  # Directly set untensorized values
            node = filled_data[path][()]
            if metadata.data_type is IDSDataType.STR and metadata.ndim == 1:
                for i in range(len(node)):
                    var[i] = node[i]
            elif not sparse:
                var[()] = node.value
            else:
                var[tuple(map(slice, node.shape))] = node.value

        else:  # Tensorize in-memory
            var.set_auto_mask(False)
            # TODO: depending on the data, tmp_var may be HUGE, we may need a more
            # efficient assignment algorithm for large and/or irregular data
            tmp_var = var[()]

            # Fill tmp_var:
            if ndim:
                for aos_coords, node in data.items():
                    tmp_var[aos_coords + tuple(map(slice, node.shape))] = node.value
            else:
                for aos_coords, node in data.items():
                    tmp_var[aos_coords] = node.value

            # Assign data to variable
            var[()] = tmp_var
            del tmp_var
