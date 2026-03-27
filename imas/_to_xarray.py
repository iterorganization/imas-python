# xarray is an optional dependency, but this module won't be imported when xarray is not
# available
import numpy
import xarray

from imas.ids_toplevel import IDSToplevel
from imas.backends.netcdf.ids_tensorizer import IDSTensorizer
from imas.ids_data_type import IDSDataType

fillvals = {
    IDSDataType.INT: numpy.int32(-(2**31) + 1),
    IDSDataType.STR: "",
    IDSDataType.FLT: numpy.nan,
    IDSDataType.CPX: numpy.nan * (1 + 1j),
}


def to_xarray(ids: IDSToplevel, *paths: str) -> xarray.Dataset:
    """See :func:`imas.util.to_xarray`"""
    # We really need an IDS toplevel element
    if not isinstance(ids, IDSToplevel):
        raise TypeError(
            f"to_xarray needs a toplevel IDS element as first argument, but got {ids!r}"
        )

    # Valid path can use / or . as separator, but IDSTensorizer expects /. The following
    # block checks if the paths are valid, and by using "metadata.path_string" we ensure
    # that / are used as separator.
    try:
        paths: list[str] = [ids.metadata[path].path_string for path in paths]
    except KeyError as exc:
        raise ValueError(str(exc)) from None

    # Converting lazy-loaded IDSs requires users to specify at least one path
    if ids._lazy and not paths:
        raise RuntimeError(
            "This IDS is lazy loaded. Please provide at least one path to convert to"
            " xarray."
        )

    # Use netcdf IDS Tensorizer to tensorize the data and determine metadata
    tensorizer = IDSTensorizer(ids, paths)
    tensorizer.include_coordinate_paths()
    tensorizer.collect_filled_data()
    tensorizer.determine_data_shapes()

    data_vars = {}
    coordinate_names = set()
    for path in tensorizer.filled_data:
        var_name = path.replace("/", ".")
        metadata = ids.metadata[path]
        if metadata.data_type in (IDSDataType.STRUCTURE, IDSDataType.STRUCT_ARRAY):
            # Metadata variables for (arrays of) structures
            if paths and path not in paths:
                continue
            dimensions = ()
            data = b""
        else:
            dimensions = tensorizer.get_dimensions(path)
            data = tensorizer.tensorize(path, fillvals[metadata.data_type])

        attrs = tensorizer.get_attributes(path, fillvals)
        if "coordinates" in attrs:
            coordinate_names.update(attrs["coordinates"].split(" "))
        data_vars[var_name] = (dimensions, data, attrs)

        # :shape array for sparse data
        if path in tensorizer.shapes and metadata.ndim:
            shape_name = f"{var_name}:shape"
            dimensions = tensorizer.get_shape_dimensions(path)
            data = tensorizer.shapes[path]
            attrs = tensorizer.get_shape_attributes(var_name)
            data_vars[shape_name] = (dimensions, data, attrs)

    # Remove coordinates from data_vars and put in coordinates mapping:
    coordinates = {}
    for coordinate_name in coordinate_names:
        coordinates[coordinate_name] = data_vars.pop(coordinate_name)

    return xarray.Dataset(data_vars, coordinates)
