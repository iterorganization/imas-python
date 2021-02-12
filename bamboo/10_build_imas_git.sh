#!/bin/sh
# Set up user-like IMAS env
set -euf -o pipefail

# Install python packages to imaspy/install
export PYTHON_INSTALL_DIR=${PYTHON_INSTALL_DIR:-`pwd`/install}
export PYTHONUSERBASE=$PYTHON_INSTALL_DIR

# Use the parts of IMAS
module load GCC/9.3.0
module load Python/3.8.2-GCCcore-9.3.0
module load Saxon-HE/9.9.1.7-Java-13
module load MDSplus/7.96.12-GCCcore-9.3.0
module load MDSplus-Java/7.96.12-GCCcore-9.3.0-Java-13
module load HDF5/1.12.0-gompi-2020a
module load Boost/1.72.0-GCCcore-9.3.0-no_mpi
module list

# install a DD locally
if [ ! -d data-dictionary ]; then
    git clone ssh://git@git.iter.org/imas/data-dictionary.git
fi
cd data-dictionary
# use the latest tagged version
export IMAS_VERSION=`git tag | sort -V | tail -n 1`
git checkout "$IMAS_VERSION"
#git clean -xf
make

cd ..
# INSTALL the access layer locally (this might take a while)
if [ ! -d access-layer ]; then
    git clone ssh://git@git.iter.org/imas/access-layer.git
fi
cd access-layer
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
make -j
cd ..

pip install --user numpy cython

cd pythoninterface
make -j
sed -e 's/imas_[^/."]*/imas/g' -i package/setup.py

# install locally
pip install --user -e package

# test if we can import the imas module
python -c 'import imas'

cd ../../
