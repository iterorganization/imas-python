import netCDF4

from imaspy.ids_data_type import IDSDataType
from imaspy.ids_metadata import IDSMetadata
from imaspy.ids_structure import IDSStructure
from imaspy.ids_toplevel import IDSToplevel


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


def aos_iter(structure: IDSStructure, paths, sizes, index):
    path, *paths = paths
    size, *sizes = sizes

    aos = structure[path]
    if len(aos) != size:
        aos.resize(size, keep=True)

    if len(paths) == 1:
        path = paths[0]
        for i in range(size):
            yield index + (i,), aos[i][path]

    else:
        for i in range(size):
            yield from aos_iter(aos[i], paths, sizes, index + (i,))


def nc2ids(group: netCDF4.Group, ids: IDSToplevel):
    var_names = sorted(group.variables)
    for var_name in var_names:
        try:
            metadata = ids.metadata[var_name]
        except KeyError:
            continue  # Assume shape variable: ignore for now

        # FIXME: this may be a gigantic array, not required for sparse data
        # FIXME: this may be a masked array when not all values are filled
        var = group[var_name]
        data = var[()]

        paths = split_on_aos(metadata)
        if len(paths) == 1:
            ids[paths[0]].value = data

        else:
            sizes = var.shape[: len(paths) - 1]
            for index, item in aos_iter(ids, paths, sizes, ()):
                item.value = data[index]
