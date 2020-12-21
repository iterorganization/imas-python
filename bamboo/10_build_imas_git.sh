#!/bin/sh
# Set up user-like IMAS env
set -euf -o pipefail

# Install python packages to imaspy/install
export PYTHON_INSTALL_DIR=${PYTHON_INSTALL_DIR:-`pwd`/install}
export PYTHONUSERBASE=$PYTHON_INSTALL_DIR

# Use the parts of IMAS
module load GCC/10.2.0
module load Python/3.8.6-GCCcore-10.2.0
module load Saxon-HE
module load MDSplus/7.96.12-GCCcore-9.3.0
module load MDSplus-Java
module load HDF5/1.12.0-gompi-2020a
module list

# install a DD locally
cd data-dictionary
# use the latest tagged version
export IMAS_VERSION=`git tag | sort -V | tail -n 1`
git checkout "$IMAS_VERSION"
#git clean -xf
make

# INSTALL the access layer locally (this might take a while)
cd ../access-layer
git checkout "$1"
#git clean -xf
if [ ! -L xml ]; then
    ln -s ../data-dictionary/ xml
fi

export UAL_VERSION=`git tag | sort -V | tail -n 1`
export IMAS_UDA=no \
    IMAS_HDF5=yes \
    IMAS_MATLAB=no \
    IMAS_MEX=no \
    IMAS_JAVA=no

export IMAS_PREFIX=`pwd`
export LIBRARY_PATH=`pwd`/lowlevel:${LIBRARY_PATH:=}
export C_INCLUDE_PATH=`pwd`/lowlevel:${C_INCLUDE_PATH:=}
export LD_LIBRARY_PATH=`pwd`/lowlevel:${LD_LIBRARY_PATH:=}

cd lowlevel
make
cd ..

pip install --user numpy cython

cd pythoninterface
make
sed -e 's/imas_[^/."]*/imas/g' -i package/setup.py

# install locally
pip install --user -e package

# test if we can import the imas module
python -c 'import imas'

cd ../../
