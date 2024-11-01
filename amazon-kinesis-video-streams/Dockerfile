# syntax=docker.io/docker/dockerfile:1

FROM docker.io/idein/actcast-rpi-app-base:buster-3 AS buster-builder

ENV DEBIAN_FRONTEND "noninteractive"
ENV DEBCONF_NOWARNINGS "yes"
RUN apt-get update -y
RUN apt-get \
    -o Dpkg::Options::="--force-confdef" \
    -o Dpkg::Options::="--force-confold" \
    upgrade -y
RUN apt-get install -y --no-install-recommends \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-bad gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-tools
RUN apt-get install -y --no-install-recommends \
    git cmake gcc g++ binutils libunwind-dev libssl-dev libcurl4-openssl-dev liblog4cplus-dev make autoconf build-essential
WORKDIR /opt
RUN git clone https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git
WORKDIR /opt/amazon-kinesis-video-streams-producer-sdk-cpp
RUN git checkout v3.4.2
RUN mkdir build
WORKDIR /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build
RUN cmake .. -DBUILD_TEST=OFF -DBUILD_GSTREAMER_PLUGIN=TRUE -DBUILD_DEPENDENCIES=OFF -DCMAKE_INSTALL_PREFIX=.
RUN make
WORKDIR /opt
RUN cp /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/libKinesisVideoProducer.so /opt \
    && cp /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/libgstkvssink.so /opt \
    && cp /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/dependency/libkvscproducer/kvscproducer-src/libcproducer.so /opt

FROM docker.io/idein/actcast-rpi-app-base:bullseye-2 AS bullseye-builder

ENV DEBIAN_FRONTEND "noninteractive"
ENV DEBCONF_NOWARNINGS "yes"
RUN apt-get update -y
RUN apt-get \
    -o Dpkg::Options::="--force-confdef" \
    -o Dpkg::Options::="--force-confold" \
    upgrade -y
RUN apt-get install -y --no-install-recommends \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-bad gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-tools
RUN apt-get install -y --no-install-recommends \
    git cmake gcc g++ binutils libunwind-dev libssl-dev libcurl4-openssl-dev liblog4cplus-dev make autoconf build-essential
WORKDIR /opt
RUN git clone https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git
WORKDIR /opt/amazon-kinesis-video-streams-producer-sdk-cpp
RUN git checkout v3.4.2
RUN mkdir build
WORKDIR /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build
RUN cmake .. -DBUILD_TEST=OFF -DBUILD_GSTREAMER_PLUGIN=TRUE -DBUILD_DEPENDENCIES=OFF -DCMAKE_INSTALL_PREFIX=.
RUN make
WORKDIR /opt
RUN cp /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/libKinesisVideoProducer.so /opt \
    && cp /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/libgstkvssink.so /opt \
    && cp /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/dependency/libkvscproducer/kvscproducer-src/libcproducer.so /opt


FROM docker.io/debian:bookworm-slim

WORKDIR /buster
COPY --from=buster-builder /opt/libKinesisVideoProducer.so /buster/
COPY --from=buster-builder /opt/libgstkvssink.so /buster/
COPY --from=buster-builder /opt/libcproducer.so /buster/

WORKDIR /bullseye
COPY --from=bullseye-builder /opt/libKinesisVideoProducer.so /bullseye/
COPY --from=bullseye-builder /opt/libgstkvssink.so /bullseye/
COPY --from=bullseye-builder /opt/libcproducer.so /bullseye/
