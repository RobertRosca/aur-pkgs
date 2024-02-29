FROM archlinux:latest

WORKDIR /src

RUN pacman -Syu --noconfirm binutils fakeroot python

COPY ./scripts /scripts
