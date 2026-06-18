SOURCE=resnet_v1_18.c
TARGET=libresnet_v1_18.so
TARGET_64BIT=libresnet_v1_18_64bit.so

.PHONY: all
all: app/$(TARGET) app/$(TARGET_64BIT)

app/$(TARGET): src/$(SOURCE) root_bullseye.tar Dockerfile
	docker build --target bullseye -t cross-rpi-aicast-bullseye .
	docker run -it --rm -d --name cross-aicast-bullseye cross-rpi-aicast-bullseye /bin/bash
	docker cp src cross-aicast-bullseye:/home/idein/src
	docker exec -it cross-aicast-bullseye armv6-rpi-linux-gnueabihf-gcc -W -Wall -Wextra -Werror -O2 -pipe -fPIC -std=c99 -I src src/$(SOURCE) -mcpu=arm1176jzf-s -mfpu=vfp -mfloat-abi=hard -shared -o $(TARGET) -lhailort -lpthread
	docker cp cross-aicast-bullseye:/home/idein/$(TARGET) app/$(TARGET)
	docker stop cross-aicast-bullseye

app/$(TARGET_64BIT): src/$(SOURCE) root.tar Dockerfile
	docker build --target bookworm -t cross-rpi-aicast-bookworm .
	docker run -it --rm -d --name cross-aicast-bookworm cross-rpi-aicast-bookworm /bin/bash
	docker cp src cross-aicast-bookworm:/home/idein/src
	docker exec -it cross-aicast-bookworm bash -c '$${TARGET_TRIPLET}-gcc -W -Wall -Wextra -Werror -O2 -pipe -fPIC -std=c99 -I $${PKG_CONFIG_SYSROOT_DIR}/usr/include -I src src/$(SOURCE) -march=armv8-a -shared -o $(TARGET_64BIT) -L$${PKG_CONFIG_SYSROOT_DIR}/usr/lib -lhailort -lpthread'
	docker cp cross-aicast-bookworm:/home/idein/$(TARGET_64BIT) app/$(TARGET_64BIT)
	docker stop cross-aicast-bookworm

.PHONY: clean
clean:
	rm -f app/$(TARGET) app/$(TARGET_64BIT)
