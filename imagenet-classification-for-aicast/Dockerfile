FROM idein/cross-rpi:armv6-slim

ENV SYSROOT /home/idein/x-tools/armv6-rpi-linux-gnueabihf/armv6-rpi-linux-gnueabihf/sysroot

ADD root.tar $SYSROOT
#RUN sudo rm $SYSROOT/usr/lib/libhailort.so
RUN sudo ln -s $SYSROOT/usr/lib/libhailort.so.4.21.0 $SYSROOT/usr/lib/libhailort.so
