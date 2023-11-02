.PHONY: all
all: app/libbilinear.so app/libmodel.so app/model.py include/model.h

app/libmodel.so app/model.py include/model.h:
	actdk compile

app/libbilinear.so: src/bilinear.c
	docker pull idein/cross-rpi:armv6-slim
	docker run -it --rm -d --name cross idein/cross-rpi:armv6-slim /bin/bash
	docker cp src cross:/home/idein/src
	docker exec -it cross armv6-rpi-linux-gnueabihf-gcc -W -Wall -Wextra -Werror -O2 -pipe -fPIC -std=c99 -I src src/bilinear.c -mcpu=arm1176jzf-s -mfpu=vfp -mfloat-abi=hard -shared -o libbilinear.so
	docker cp cross:/home/idein/libbilinear.so app/libbilinear.so
	docker stop cross

.PHONY: clean
clean:
	rm -f app/*.so
	rm -f app/model.py
	rm -f include/model.h
