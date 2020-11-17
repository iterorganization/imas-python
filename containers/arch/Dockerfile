# Install IMAS, MDSPlus and IMASPy in a docker container based on arch linux
FROM archlinux:latest
LABEL maintainer="Daan van Vugt <dvanvugt@ignitioncomputing.com>"

RUN pacman -Sy --noconfirm --needed base-devel git sudo pyalpm python-pip && \
    pip install pikaur cython numpy

RUN python -m pikaur -S --noconfirm --needed blitz saxon-he

# arch linux cython had an issue, get it with pip...
RUN useradd builduser -m && \
    passwd -d builduser && \
    cd /home/builduser

WORKDIR MDSplus
RUN wget https://raw.githubusercontent.com/DaanVanVugt/mdsplus-pkgbuild/main/PKGBUILD
RUN makepkg -ir
