# Use the parts of IMAS
# This is stricly versioned to catch errors early
# Based on IMAS/3.32.1-4.9.1-2020b
set -xe
module load GCCcore/10.2.0
module load Python/3.8.6-GCCcore-10.2.0
module load MDSplus/7.96.17-GCCcore-10.2.0
module load HDF5/1.10.7-iimpi-2020b  # todo: Intel MPI version?
module load Boost/1.74.0-GCCcore-10.2.0

# Extra modules that we need to build
module load MDSplus-Java/7.96.17-GCCcore-10.2.0-Java-11
module load Saxon-HE/10.3-Java-11
# Very ugly way to just get saxon-he-10.3.jar, which we need for the DD
export SAXONJARFILE=`echo $CLASSPATH | cut -d: -f4 | rev | cut -d/ -f1 | rev`
echo [INFO] Set SAXONJARFILE to $SAXONJARFILE

module list
