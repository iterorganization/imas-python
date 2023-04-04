# Use the parts of IMAS
# This is stricly versioned to catch errors early
set -xeuf -o pipefail

# Bizarrely we need to (re)load pgi before unloading it - some obscure effect of IMAS/3.25.0

############################################################################
# Based on /home/pknight/jintrac/ci_pgi/modules/jintrac/heimdall.gfortran7 #
############################################################################
#module load pgi
#module unload pgi
#module load gcc/7.5.0
#module load openmpi


########################################################################
# Based on /home/pknight/jintrac/ci_pgi/modules/jintrac/heimdall.ifort #
########################################################################
# N.B. imas-modules/2.0 loads imas-setup, which performs a 'module purge'
# here use custom JINTRAC version which does not
module load imas-setup-jet/1.0

module unload pgi
module load ifort
module load nag
#module load openmpi # Check if we need this

module swap python/3.7
# module load jintrac_host/heimdall # I think we need this

module load mdsplus/7.92.0/gcc/4.8.5
module load mdsplus-devel
export JINTRAC_IMASMODULE=IMAS/3.28.1/AL/4.7.2
#module load ${JINTRAC_IMASMODULE}
#
#setenv JINTRAC_CONFIG  $env(JINTRAC_DIR)/config/heimdall.ifort
#
## Compiler-specific library path additions
#
#append-path LD_LIBRARY_PATH /usr/local/depot/hsl-ifort/lib
#append-path LD_LIBRARY_PATH /usr/local/depot/NAGMark23/fll6i23dc/rtl
#
## GRID2D requirement
#append-path LD_LIBRARY_PATH /usr/local/depot/netcdf-4.4.1-ifort12/lib
#
## Recover module state prior to 'module load jintrac'
#if { [ module-info mode remove ] == 1 } {
#   module unload blitz uda imas-setup-jet
#   module swap python/2.7.5
#   # The following does not work here for reasons unknown:
#   #module load mdsplus
#   #module load pgi
#   #module load openmpi
#   #module load nag
#   #module load flush/2.2.0
#}
#
#
##module load GCCcore/10.2.0
##module load Python/3.8.6-GCCcore-10.2.0
##module load MDSplus/7.96.17-GCCcore-10.2.0
##module load HDF5/1.10.7-iimpi-2020b  # todo: Intel MPI version?
##module load Boost/1.74.0-GCCcore-10.2.0
##
### Extra modules that we need to build
##module load MDSplus-Java/7.96.17-GCCcore-10.2.0-Java-11
module load saxonhe
##
### Documentation for data-dictionairy
##module load Doxygen/1.8.20-GCCcore-10.2.0
##
### Very ugly way to just get saxon-he-10.3.jar, which we need for the DD
##export SAXONJARFILE=`echo $CLASSPATH | cut -d: -f4 | rev | cut -d/ -f1 | rev`
##echo [INFO] Set SAXONJARFILE to $SAXONJARFILE

module list
