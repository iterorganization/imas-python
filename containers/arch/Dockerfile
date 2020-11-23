# Install IMAS, MDSPlus and IMASPy in a docker container based on arch linux
FROM archlinux:latest AS base
LABEL maintainer="Daan van Vugt <dvanvugt@ignitioncomputing.com>"

RUN pacman --sync --noconfirm --refresh --sysupgrade && \
    pacman --sync --noconfirm --needed python base-devel git wget python-pip cmake boost jdk11-openjdk jre11-openjdk gcc-fortran libxslt hdf5 doxygen vim && \
    find /var/cache/pacman/pkg -mindepth 1 -delete

RUN pip install --no-cache cython numpy

###################################################
# Build the build image with IMAS-AL dependencies #
###################################################
FROM base AS build
#RUN useradd -ms /bin/bash builduser
USER nobody
WORKDIR /tmp

# Build packages
RUN mkdir -p blitz && cd blitz && \
    wget --quiet "https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=blitz"  -O PKGBUILD && \
    makepkg

# We need saxon-he 9 since IMAS DD and AL build tools require this (until _after_ version 3.30.0 for DD and 4.8.5 for AL)
RUN mkdir -p saxon-he && cd saxon-he && \
    wget --quiet "https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=saxon-he&id=784e5befd2fe1a4be67e2efb342dd2d29da5a688" -O PKGBUILD && \
    wget --quiet "https://aur.archlinux.org/cgit/aur.git/plain/saxon-xquery.sh?h=saxon-he&id=784e5befd2fe1a4be67e2efb342dd2d29da5a688" -O saxon-xquery.sh && \
    wget --quiet "https://aur.archlinux.org/cgit/aur.git/plain/saxon-xslt.sh?h=saxon-he&id=784e5befd2fe1a4be67e2efb342dd2d29da5a688" -O saxon-xslt.sh && \
    makepkg

RUN mkdir -p MDSplus && cd MDSplus && \
    wget https://raw.githubusercontent.com/DaanVanVugt/mdsplus-pkgbuild/main/PKGBUILD -q && \
    makepkg

# Install packages in root dir
USER root
RUN pacman -U --noconfirm */*.pkg.tar.zst && \
    rm -rf /tmp/*
WORKDIR /root/

#####################
# Build the IMAS-DD #
#####################
FROM build AS data_dictionary

# Fetch IMAS packages from this directory (download them beforehand)
# Since these are not publicly accessible we have to do it this way
ADD data-dictionary/ /root/data-dictionary
ENV IMAS_VERSION 3.30.0
ENV CLASSPATH=/usr/share/java/saxon/saxon9he.jar
RUN cd /root/data-dictionary && \
    git checkout "$IMAS_VERSION" && \
    make
# 3.30.0 and lower only work with saxon9he.jar
#TODO install a second DD version

#####################
# Build the IMAS-AL #
#####################
FROM build AS access_layer

ADD access-layer/ /root/access-layer
COPY --from=data_dictionary /root/data-dictionary/ /root/access-layer/xml/

ENV UAL_VERSION=4.8.5
ENV IMAS_UDA=no \
    IMAS_HDF5=yes \
    IMAS_MATLAB=no \
    IMAS_MEX=no \
    IMAS_JAVA=no
# where should we place jTraverser.jar so we don't need the classpath?
ENV CLASSPATH=/usr/java/classes/jTraverser.jar
# 4.8.5 and up
RUN cd /root/access-layer && \
    git checkout "$UAL_VERSION" && \
    make -j`nproc`

FROM access_layer AS python_hli
COPY --from=access_layer /root/access-layer /root/access-layer

ENV IMAS_PREFIX=/root/access-layer/ \
    IMAS_VERSION=3.30.0
ENV LIBRARY_PATH=/root/access-layer/lowlevel/ \
    C_INCLUDE_PATH=/root/access-layer/lowlevel/ \
    LD_LIBRARY_PATH=/root/access-layer/lowlevel/

RUN cd /root/access-layer/pythoninterface/package/ && \
    sed -e 's/imas_[^/."]*/imas/g' -i setup.py && \
    pip install -e .

# ADD IMASPy
#RUN git clone https://gitlab.com/klimex/imaspy.git && \
    #pip install -e imaspy[backends_xarray,test]
ADD imaspy/ /root/imaspy
RUN pip install -e imaspy[backends_al,backends_xarray,test]
