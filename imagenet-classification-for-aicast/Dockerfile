FROM idein/cross-rpi:armv6-slim AS bullseye

ENV SYSROOT=/home/idein/x-tools/armv6-rpi-linux-gnueabihf/armv6-rpi-linux-gnueabihf/sysroot

ADD root_bullseye.tar $SYSROOT
RUN sudo rm -f $SYSROOT/usr/lib/libhailort.so \
 && sudo ln -s $SYSROOT/usr/lib/libhailort.so.4.10.0 $SYSROOT/usr/lib/libhailort.so


FROM debian:bookworm-slim AS bookworm

ENV DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y --no-install-recommends sudo crossbuild-essential-arm64 pkg-config

RUN useradd -m idein \
 && echo idein:idein | chpasswd \
 && adduser idein sudo \
 && echo 'idein ALL=NOPASSWD: ALL' >> /etc/sudoers.d/idein

USER idein
WORKDIR /home/idein
ENV HOME=/home/idein

ENV TARGET_TRIPLET=aarch64-linux-gnu
ENV PKG_CONFIG_SYSROOT_DIR=${HOME}/x-tools/${TARGET_TRIPLET}/sysroot

RUN mkdir -p "${PKG_CONFIG_SYSROOT_DIR}"
ADD root.tar ${PKG_CONFIG_SYSROOT_DIR}
RUN sudo ln -s ${PKG_CONFIG_SYSROOT_DIR}/usr/lib/libhailort.so.4.21.0 ${PKG_CONFIG_SYSROOT_DIR}/usr/lib/libhailort.so

CMD ["/bin/bash"]
