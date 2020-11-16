# This file is part of IMASPy.
#
# IMASPy is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IMASPy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with IMASPy.  If not, see <https://www.gnu.org/licenses/>.
import sys
import os
import logging

from IPython import embed
import numpy
import numpy as np

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.WARNING)

if __name__ == "__main__":
    # from imaspy.ids_classes import *
    # MVP, get a slice
    # So for example be able to run
    # import imaspy as imas
    # input = imas.ids(shot,run_in)
    # input.open_env(input_user_or_path,input_database,’3’)
    # input.equilibrium.getSlice(time_slice, 1)

    # Existing workflow example
    shot = 130012
    # input_user_or_path = 'public'
    input_database = "iter"
    time_slice = 200
    occurence = 0

    # Test example
    TEST_SHOT = 1
    TEST_RUN = 2
    backend = 3
    BACKEND_ID_0 = 10
    NO_BACKEND = BACKEND_ID_0
    ASCII_BACKEND = BACKEND_ID_0 + 1
    MDSPLUS_BACKEND = BACKEND_ID_0 + 2
    HDF5_BACKEND = BACKEND_ID_0 + 3
    MEMORY_BACKEND = BACKEND_ID_0 + 4
    UDA_BACKEND = BACKEND_ID_0 + 5
    # backend = MEMORY_BACKEND
    backend = MDSPLUS_BACKEND
    ACCESS_PULSE_0 = 40
    FORCE_CREATE_PULSE = ACCESS_PULSE_0 + 3
    input_user_or_path = "vandepk"

    # Old API
    # import matplotlib.pyplot as plt
    style = "old"
    style = "new"
    if style == "old":
        # import imas_3_28_1_ual_4_7_2_dev38 as imas
        run_in = 0
        try:
            # Try loading Karels special library
            import imas_3_28_1_ual_4_7_2_dev36 as imas
        except ImportError:
            # Load the regular IMAS library
            import imas

        imas_entry = imas.ids(shot, run_in)
        idx = imas_entry.create_env_backend(
            input_user_or_path, input_database, "3", backend
        )
    else:
        # New API
        run_in = 1
        # 4.4.1 Initializing an empty IDS
        import imaspy as imas
        from pathlib import Path

        imas.ids = imas.ids_classes.IDSRoot  # Enable old-style syntax

        IMAS_PREFIX = os.getenv("IMAS_PREFIX")
        if not IMAS_PREFIX or not os.path.isdir(IMAS_PREFIX):
            logger.warning(
                "IMAS_PREFIX is unset or is not a directory. Points to {!s}. Fall back to 'karel paths'!".format(
                    IMAS_PREFIX
                )
            )
            idsdef_dir = Path(os.path.dirname(__file__)) / Path(
                "../../../../working/imas-data-dictionary/"
            )
            idsdef = Path(idsdef_dir) / Path("IDSDef.xml")
        else:
            imas_prefix = Path(os.getenv("IMAS_PREFIX"))
            imas_include = imas_prefix.joinpath("include")
            idsdef = imas_include.joinpath("IDSDef.xml")
        imas_entry = imas.ids(shot, run_in, xml_path=idsdef, verbosity=2)
        idx = imas_entry.create_env_backend(
            input_user_or_path, input_database, "3", backend
        )
    # This should then support accessing an IDS using idsVar.<IDSname>.<IDSfield>

    # 5.5 Opening an existing Data Entry
    # imas_entry.open_env(input_user_or_path, input_database, '3')

    # 5.6 Opening a remote Data Entry using the UDA backend
    # imas_entry = imas.ids(54178, 0)
    # imas_entry.open_public('WEST')

    # 5.7 Closing an opened Data Entry
    # [retstatus] = imas_entry.close()

    # 4.4.2 Copying a variable to a new IDS. Not deepcopy! Proposed API:
    # idsVar2.equilibrium.copyValues(idsVar)

    # 4.4.3 Deallocation
    # Using python build-in management, or del var

    # 5.4 Creating a new data entry
    # Put mandatory top-level entry
    ids = imas_entry.equilibrium
    # ids.ids_properties.homogeneous_time = 2
    time = imas._libs.imasdef.IDS_TIME_MODE_HOMOGENEOUS
    ids.ids_properties.homogeneous_time = time

    ids.put()
    print(
        "Original ids.ids_properties.homogeneous_time:",
        ids.ids_properties.homogeneous_time,
    )
    ids.ids_properties.homogeneous_time = 9999
    print(
        "Changed ids.ids_properties.homogeneous_time:",
        ids.ids_properties.homogeneous_time,
    )
    ids.get()
    print(
        "After re-get ids.ids_properties.homogeneous_time:",
        ids.ids_properties.homogeneous_time,
    )

    # 5.8 Putting an IDS
    # 5.10 Deleting an IDS # ids.put() deletes the IDS, so calls deleteData(self, occurence)
    # 5.11 Getting an IDS # Easiest to show the put works by showing a get!

    # Creating a nested data entry
    print(
        "Pre put ids.ids_properties.version_put.access_layer:",
        ids.ids_properties.version_put.access_layer,
    )
    ids.ids_properties.version_put.access_layer = "imaspy"
    ids.put()
    print(
        "Post put ids.ids_properties.version_put.access_layer:",
        ids.ids_properties.version_put.access_layer,
    )
    ids.get()
    print(
        "Post get ids.ids_properties.version_put.access_layer:",
        ids.ids_properties.version_put.access_layer,
    )

    # Deeper fields
    # Set time vector
    print("Pre put ids.time:", ids.time)
    ids.time = np.array([0.1, 0.2, 0.3])
    ids.time = ids.time + 2
    ids.put()
    print("Post put ids.time:", ids.time)
    ids.time = [12345678]  # Scamble
    ids.get()
    print("Post get ids.time:", ids.time)

    # And an array
    print("Pre put ids.vacuum_toroidal_field.b0:", ids.vacuum_toroidal_field.b0)
    ids.vacuum_toroidal_field.b0 = np.array([1, 2, 3])
    ids.put()
    print("Post put ids.vacuum_toroidal_field.b0:", ids.vacuum_toroidal_field.b0)
    # Scramble
    ids.vacuum_toroidal_field.b0 = [-98767890]
    ids.get()
    print("Post get ids.vacuum_toroidal_field.b0:", ids.vacuum_toroidal_field.b0)

    # We can do fancy math even!
    print("ids.vacuum_toroidal_field.b0 + 2:", ids.vacuum_toroidal_field.b0 + 2)

    ## Set beyond a struct array
    print("Pre put ids.time_slice:", ids.time_slice)
    ids.time_slice.resize(1)
    ids.time_slice[0].profiles_1d.psi = np.array([0, 0.5, 1.5])
    ids.time_slice[0].time = 0.1
    ids.put()
    print("Post put ids.time_slice[0].time:", ids.time_slice[0].time)
    print(
        "Post put ids.time_slice[0].profiles_1d.psi:", ids.time_slice[0].profiles_1d.psi
    )
    # Scramble
    ids.time_slice[0].time = [-12344567]
    ids.time_slice[0].profiles_1d.psi = [-98767890]
    ids.get()
    print("Post get ids.time_slice[0].time:", ids.time_slice[0].time)
    print(
        "Post get ids.time_slice[0].profiles_1d.psi:", ids.time_slice[0].profiles_1d.psi
    )

    ids.time_slice[0].profiles_2d.resize(1)
    ids.time_slice[0].profiles_2d[0].grid_type.name = "I am grid"
    ids.put()
    print(
        "Post put ids.time_slice[0].profiles_2d[0].grid_type.name:",
        ids.time_slice[0].profiles_2d[0].grid_type.name,
    )
    ## Scramble
    ids.time_slice[0].profiles_2d[0].grid_type.name = "stuff"

    ids.get()
    print(
        "Post get ids.time_slice[0].profiles_2d[0].grid_type.name:",
        ids.time_slice[0].profiles_2d[0].grid_type.name,
    )

    # time_slice.coordinate_system.grid.volume_element 2D_FLT
    # time_slice.coordinate_system.tensor_covariant 4D_FLT

    # 5.9 Putting an IDS progressively in a time loop
    # Expect the IDS variable to contain a single slice in any non-empty dynamic nodes
    # So, start with a single .put, then progressive put_slice IN STRICT TIME ORDER

    # 5.12 Getting a slice
    # imas_entry.pf_active.getSlice(0.1, 2)

    # 5.13 Getting units of a note
    # Slash-separated path, ignore arrays, as all units in array are the same
    # units = get_units(ids, node_path)

    # 5.14 Getting a subset of an IDS
    # Smart datapath, so path/to/array(idx)/field
    # Smart datapath, so path/to/array(x:y)/field
    # partialGet

    # 5.15 Selecting the backend
    # MDSPLUS, MEMORY, UDA, ASCII
    # MAGIC, ignore for now?

    print("Done!")
