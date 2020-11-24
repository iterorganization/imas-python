# -------------------------------------------------
# PYTHON WRAPPER TO CALL PION (AND OTIONALLY NEMO)
# -------------------------------------------------

import copy

# NEEDED MODULES
import os
import sys

from IPython import embed  # Convinience

# INPUT/OUTPUT CONFIGURATION
shot = 44
run_in = 33
run_out = 133
input_user_or_path = "public"
input_database = "ITER_MD"
output_user_or_path = os.getenv("USER")
output_database = input_database

# DISPLAY SIMULATION INFORMATION
print("---------------------------------")
print("shot                = ", shot)
print("run_in              = ", run_in)
print("run_out             = ", run_out)
print("input_user_or_path  = ", input_user_or_path)
print("input_database      = ", input_database)
print("output_user_or_path = ", output_user_or_path)
print("output_database     = ", output_database)
print("---------------------------------")

# IF THE OUTPUT DATABASE DOES NOT EXIST: CREATE IT
if output_user_or_path == os.getenv("USER"):
    output_folder = os.getenv("HOME") + "/public/imasdb/" + output_database + "/3/0"
else:
    output_folder = output_user_or_path + "/" + output_database + "/3/0"
if os.path.isdir(output_folder) == False:
    print("-- Create local database for output file " + output_folder, file=sys.stdout)
    os.makedirs(output_folder)

# IMAS DATA VERSION
version = os.getenv("IMAS_VERSION")[0]

# OPEN INPUT DATAFILE
style = "old"
style = "new"
if style == "old":
    import imas

    print("=> Open input datafile")
    input = imas.DBEntry(
        imas.imasdef.MDSPLUS_BACKEND, input_database, shot, run_in, input_user_or_path
    )
    input.open()

    # READ NBI IDS FROM INPUT DATAFILE
    print("=> Read nbi IDS")
    input_nbi = input.get("nbi")

    # COPY THE NBI IDS (IN VIEW OF MODIFYING IT)
    output_nbi = input_nbi  # I don't think this actually makes a copy!!!

    # CREATE OUTPUT DATAFILE
    print("=> Create output datafile")
    output = imas.DBEntry(
        imas.imasdef.MDSPLUS_BACKEND,
        output_database,
        shot,
        run_out,
        output_user_or_path,
    )
    output.create()

    # WRITE NBI IDS IN OUTPUT DATAFILE
    print("=> Write nbi IDS")
    output.put(output_nbi)

    # CLOSE FILES
    input.close()
    output.close()
    print("Done.")
else:
    import imaspy as imas
    from imas.imasdef import MDSPLUS_BACKEND
    from pathlib import Path

    imas.ids = imas.ids_classes.IDSRoot  # Enable old-style syntax
    imas_prefix = Path(os.getenv("IMAS_PREFIX"))
    imas_include = imas_prefix.joinpath("xml")
    idsdef = imas_include.joinpath("IDSDef.xml")
    input = imas.ids(shot, run_in, xml_path=idsdef, verbosity=2)  # Create a empty IDSs
    input.open_env_backend(
        input_user_or_path, input_database, "3", MDSPLUS_BACKEND
    )  # Start a new 'pulse action', linking IDSs to input database

    # READ NBI IDS FROM INPUT DATAFILE
    input_nbi = input.nbi  # Make a convinient name for NBI IDS
    input_nbi.get()  # Fill empty nbi structure from database

    output_nbi = copy.deepcopy(
        input_nbi
    )  # This really copies the IDS. Not for old API though..

    ## Do a hacky thing to link to a new file now, should mirror the Python HLI API I guess
    output = output_nbi._parent
    output.create_env_backend(
        output_user_or_path, output_database, "3", MDSPLUS_BACKEND
    )  # Start a new 'pulse acting', linking IDSs to output database

    # embed() # Tip: Use IPython's embed() or ipdb for autocomplete, colors, etc.
    unit = output_nbi["unit"][1]
    unit["name"] = "banana"

    # WRITE NBI IDS IN OUTPUT DATAFILE
    output_nbi.put()

    # CLOSE FILES
    input.close()
    output.close()
    print("Done.")
