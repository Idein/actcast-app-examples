FROM idein/actcast-rpi-app-base:bookworm-1 AS python-env

ENV DEBIAN_FRONTEND noninteractive
ENV VIRTUAL_ENV /venv
ENV PATH /venv/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends python3-pip python3-venv python3-dev gcc

RUN python3 -m venv --system-site-packages /venv

RUN pip3 install actfw-raspberrypi
COPY hailort-4.21.0-cp311-cp311-linux_aarch64.whl /tmp/
RUN pip3 install /tmp/hailort-4.21.0-cp311-cp311-linux_aarch64.whl

RUN pip3 list && pip3 check

FROM idein/actcast-rpi-app-base:bookworm-1

ENV DEBIAN_FRONTEND noninteractive
ENV VIRTUAL_ENV /venv
ENV PATH /venv/bin:$PATH

RUN apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y libv4l-0 libv4lconvert0 python3 fbset fonts-dejavu-core libatomic1 \
 && apt-get clean \
 && apt-get autoclean \
 && apt-get autoremove -y \
 && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

COPY --from=python-env /venv /venv

ADD root_4.21.0.aarch64.tar /

WORKDIR /root

COPY app ./

STOPSIGNAL SIGTERM
RUN chmod +x /root/main /root/healthchecker
ENTRYPOINT ["/root/main"]
HEALTHCHECK --interval=10s --timeout=10s --retries=3 --start-period=60s CMD /root/healthchecker
