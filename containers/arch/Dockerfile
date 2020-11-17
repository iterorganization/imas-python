# Install IMAS, MDSPlus and IMASPy in a docker container based on arch linux
FROM archlinux:latest
LABEL maintainer="Daan van Vugt <dvanvugt@ignitioncomputing.com>"

RUN pacman --sync --noconfirm --refresh --sysupgrade && \
    pacman --sync --noconfirm --needed python base-devel git python-pip wget && \
    find /var/cache/pacman/pkg -mindepth 1 -delete

RUN pip install --no-cache cython numpy

RUN useradd -ms /bin/bash builduser

USER builduser
WORKDIR /home/builduser/blitz
RUN wget "https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=blitz" && \
    makepkg -i

WORKDIR /home/builduser/saxon-he
RUN wget "https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=saxon-he" && \
    makepkg -i

WORKDIR /home/builduser/MDSplus
RUN wget https://raw.githubusercontent.com/DaanVanVugt/mdsplus-pkgbuild/main/PKGBUILD && \
    makepkg -ir
