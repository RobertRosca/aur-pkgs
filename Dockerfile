FROM archlinux:latest

WORKDIR /src

RUN pacman -Syu --noconfirm && \
    pacman -S --needed --noconfirm binutils fakeroot python sudo && \
    pacman -Scc --noconfirm

RUN useradd -m builder && \
    passwd -d builder && \
    echo "builder ALL=(ALL) ALL" > /etc/sudoers.d/builder && \
    chmod 0440 /etc/sudoers.d/builder

USER builder

WORKDIR /home/builder

CMD ["/bin/bash"]
