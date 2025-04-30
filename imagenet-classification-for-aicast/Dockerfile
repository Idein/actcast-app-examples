FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y --no-install-recommends sudo crossbuild-essential-arm64 pkg-config

# add idein user
RUN useradd -m idein \
 && echo idein:idein | chpasswd

# sudo setting
RUN adduser idein sudo \
 && echo 'idein ALL=NOPASSWD: ALL' >> /etc/sudoers.d/idein

USER idein
WORKDIR /home/idein
ENV HOME=/home/idein


ENV TARGET_TRIPLET="aarch64-linux-gnu"
ENV PKG_CONFIG_SYSROOT_DIR="${HOME}/x-tools/${TARGET_TRIPLET}/sysroot"

RUN mkdir -p "${PKG_CONFIG_SYSROOT_DIR}"
ENV HAILORT_VERSION=4.21.0
COPY hailort_${HAILORT_VERSION}_arm64.deb /tmp/
RUN dpkg -x /tmp/hailort_${HAILORT_VERSION}_arm64.deb "${PKG_CONFIG_SYSROOT_DIR}"
RUN ln -s ${PKG_CONFIG_SYSROOT_DIR}/usr/lib/libhailort.so.${HAILORT_VERSION} ${PKG_CONFIG_SYSROOT_DIR}/usr/lib/libhailort.so

CMD ["/bin/bash"]
