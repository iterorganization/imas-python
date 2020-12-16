#!/bin/sh
# Bamboo Build script

set -x

# Set up environment
. /usr/share/Modules/init/sh
module use /work/imas/etc/modulefiles
module use /work/imas/etc/modules/all
module purge

# Use the develop IMAS split repo and pytest
module load Python/3.8.2-GGCcore-9.3.0
module load AL-Python-lib/0.1.0-foss-2020a-Python-3.8.2
module load AL-Cython/0.1.0-foss-2020a-Python-3.8.2
module load pytest/3.8.0-foss-2018a-Python-3.6.4

tmp_dir=$(mktemp -d -p $bamboo_build_working_directory -t ci-XXX)

ids_path_old=${ids_path}

export ids_path="${tmp_dir};$ids_path"

export PYTHONPATH=$bamboo_build_working_directory/install:${PYTHONPATH}

make install # installs into local /install folder

# Run tests and generate reports
make tests
