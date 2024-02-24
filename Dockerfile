FROM archlinux:latest

WORKDIR /src

RUN pacman -Syu --noconfirm binutils fakeroot python

COPY ./build-in-docker.sh /build-in-docker.sh

CMD ["bash", "/build-in-docker.sh"]
