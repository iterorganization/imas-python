from typing import Dict, List
import awkward as ak
import numpy as np
from . import IDSFactory
from .ids_toplevel import IDSToplevel
from .backends.netcdf.ids_tensorizer import IDSTensorizer

def recursively_put(location, value, ids):
    # time_slice.profiles_1d.psi
    if "." in location:
        position, sub_location = location.split(".", 1)
        sub_ids = getattr(ids, position)
        if hasattr(sub_ids, "size"):
            N = len(value)
            if sub_ids.size == 0:
                sub_ids.resize(N)
            elif sub_ids.size != N:
                raise ValueError(
                    f"""Inconsistent size across flat entries {location}, {N} (flat) vs. ids {sub_ids.size}!
"""
                )
            # Need to iterate over indices (e.g. equilibrium.time_slice[:].)
            for index in range(N):
                recursively_put(sub_location, value[index], sub_ids[index])
        else:
            # Need to set an attribute
            # Now get the new substring, e.g. time_slice
            position, sub_location = location.split(".", 1)
            recursively_put(sub_location, value, sub_ids)
    else:
        setattr(ids, location, value)
    return ids


def wrangle(flat: Dict, version="3.41.0") -> Dict[str, IDSToplevel]:
    wrangled = {}
    factory = IDSFactory(version)
    for key in flat:
        ids, location = key.split(".", 1)
        if ids not in wrangled:
            wrangled[ids] = getattr(factory, ids)()
        wrangled[ids] = recursively_put(location, flat[key], wrangled[ids])
    return wrangled

def split_location_across_ids(locations: List[str]) -> Dict[str, List[str]]:
    ids_locations = {}
    for location in locations:
        ids, path = location.split(".",1)
        if ids not in ids_locations:
            ids_locations[ids] = []
        ids_locations[ids].append(path.replace(".","/") )
    return ids_locations

def unwrangle(
    locations: List[str], ids_dict: Dict[str, IDSToplevel], version="3.41.0"
) -> Dict[str, ak.Array | np.ndarray]:
    flat = {}  
    ids_locations = split_location_across_ids(locations)
    for key in ids_locations:
        tensorizer = IDSTensorizer(ids_dict[key], ids_locations[key])
        tensorizer.include_coordinate_paths()
        tensorizer.collect_filled_data()
        tensorizer.determine_data_shapes()
        # Add IDS conversion
        for ids_location in ids_locations[key]:
            location = key + "." + ids_location.replace("/", ".")
            values = tensorizer.awkward_tensorize(ids_location)
            if hasattr(values, "__getattr__"):
                # Not a scalar, e.g. homogenous_time
                try:
                    flat[location] = np.asarray(values)
                except ValueError as e:
                    flat[location] = ak.Array(values)
            else:
                flat[location] = values
    return flat
