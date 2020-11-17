# Install IMAS, MDSPlus and IMASPy in a docker container based on arch linux
FROM archlinux:latest
LABEL maintainer="Daan van Vugt <dvanvugt@ignitioncomputing.com>"

RUN pacman --sync --noconfirm --refresh --sysupgrade && \
    pacman --sync --noconfirm --needed python base-devel git python-pip wget cmake boost java-runtime-headless gcc-fortran && \
    find /var/cache/pacman/pkg -mindepth 1 -delete

RUN pip install --no-cache cython numpy

RUN useradd -ms /bin/bash builduser

USER builduser
WORKDIR /home/builduser
RUN mkdir -p blitz && cd blitz && \
    wget --quiet "https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=blitz"  -O PKGBUILD && \
    makepkg

RUN mkdir -p saxon-he && cd saxon-he && \
    wget --quiet "https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=saxon-he" -O PKGBUILD && \
    wget --quiet "https://aur.archlinux.org/cgit/aur.git/plain/saxon-xquery.sh?h=saxon-he" -O saxon-xquery.sh && \
    wget --quiet "https://aur.archlinux.org/cgit/aur.git/plain/saxon-xslt.sh?h=saxon-he" -O saxon-xslt.sh && \
    makepkg

RUN mkdir -p MDSplus && cd MDSplus && \
    wget https://raw.githubusercontent.com/DaanVanVugt/mdsplus-pkgbuild/main/PKGBUILD -q && \
    makepkg

USER root
WORKDIR /home/builduser
RUN pacman -U --noconfirm */*.pkg.tar.zst
