FROM alpine:3.18

RUN echo "@testing http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk --update add gstreamer-tools gst-plugins-base gst-plugins-good gst-plugins-ugly gst-plugins-bad gst-rtsp-server@testing
