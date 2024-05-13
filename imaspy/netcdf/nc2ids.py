from typing import Iterator, List, Tuple

import netCDF4

from imaspy.ids_base import IDSBase
from imaspy.ids_data_type import IDSDataType
from imaspy.ids_metadata import IDSMetadata
from imaspy.ids_structure import IDSStructure
from imaspy.ids_toplevel import IDSToplevel
from imaspy.netcdf.nc_metadata import NCMetadata


def split_on_aos(metadata: IDSMetadata):
    paths = []
    curpath = metadata.name

    item = metadata
    while item._parent.data_type is not None:
        item = item._parent
        if item.data_type is IDSDataType.STRUCT_ARRAY:
            paths.append(curpath)
            curpath = item.name
        else:
            curpath = f"{item.name}/{curpath}"
    paths.append(curpath)
    return paths[::-1]


IndexedNode = Tuple[Tuple[int, ...], IDSBase]


def tree_iter(structure: IDSStructure, metadata: IDSMetadata) -> Iterator[IndexedNode]:
    paths = split_on_aos(metadata)
    if len(paths) == 1:
        yield (), structure[paths[0]]
    else:
        yield from _tree_iter(structure, paths, ())


def _tree_iter(
    structure: IDSStructure, paths: List[str], curindex: Tuple[int, ...]
) -> Iterator[IndexedNode]:
    path, *paths = paths
    aos = structure[path]

    if len(paths) == 1:
        path = paths[0]
        for i, node in enumerate(aos):
            yield curindex + (i,), node[path]

    else:
        for i, node in enumerate(aos):
            yield from _tree_iter(node, paths, curindex + (i,))


def nc2ids(group: netCDF4.Group, ids: IDSToplevel):
    var_names = list(group.variables)
    # FIXME: ensure that var_names are sorted properly
    # Current assumption is that creation-order is fine
    homogeneous_time = group["ids_properties.homogeneous_time"][()] == 1
    ncmeta = NCMetadata(ids.metadata)

    for var_name in var_names:
        if var_name.endswith(":shape"):
            continue  # TODO: validate that this is used

        # FIXME: error handling:
        metadata = ids.metadata[var_name]

        # TODO: validate metadata (units, etc.) conforms to DD?

        if metadata.data_type is IDSDataType.STRUCTURE:
            continue  # This only contains DD metadata we already know

        var = group[var_name]
        if metadata.data_type is IDSDataType.STRUCT_ARRAY:
            if "sparse" in var.ncattrs():
                shapes = group[var_name + ":shape"]
                for index, node in tree_iter(ids, metadata):
                    node.resize(shapes[index][0])

            else:
                # FIXME: extract dimension name from nc file?
                dim = ncmeta.get_dimensions(metadata.path_string, homogeneous_time)[-1]
                size = group.dimensions[dim].size
                for _, node in tree_iter(ids, metadata):
                    node.resize(size)

            continue

        # FIXME: this may be a gigantic array, not required for sparse data
        # FIXME: this may be a masked array when not all values are filled
        var = group[var_name]
        data = var[()]
        data

        if metadata.path_string not in ncmeta.aos:
            # Shortcut for assigning untensorized data
            ids[metadata.path] = data

        elif "sparse" in var.ncattrs():
            if metadata.ndim:
                shapes = group[var_name + ":shape"]
                for index, node in tree_iter(ids, metadata):
                    shape = shapes[index]
                    if all(shape):
                        node.value = data[index + tuple(map(slice, shapes[index]))]
            else:
                for index, node in tree_iter(ids, metadata):
                    value = data[index]
                    if value != getattr(var, "_FillValue", None):
                        node.value = data[index]

        else:
            for index, node in tree_iter(ids, metadata):
                node.value = data[index]
