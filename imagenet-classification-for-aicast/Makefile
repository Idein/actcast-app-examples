SOURCE=resnet_v1_18.c
TARGET=libresnet_v1_18.so

.PHONY: all
all: app/$(TARGET)

app/$(TARGET): src/$(SOURCE)
	docker build -t cross-rpi .
	docker run -it --rm -d --name cross cross-rpi /bin/bash
	docker cp src cross:/home/idein/src
	docker exec -it cross armv6-rpi-linux-gnueabihf-gcc -W -Wall -Wextra -Werror -O2 -pipe -fPIC -std=c99 -I src src/$(SOURCE) -mcpu=arm1176jzf-s -mfpu=vfp -mfloat-abi=hard -shared -o $(TARGET) -lhailort -lpthread
	docker cp cross:/home/idein/$(TARGET) app/$(TARGET)
	docker stop cross

.PHONY: clean
clean:
	rm -f app/$(TARGET)
