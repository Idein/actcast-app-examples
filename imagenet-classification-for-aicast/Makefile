SOURCE=resnet_v1_18.c
TARGET=libresnet_v1_18.so

.PHONY: all
all: app/$(TARGET)

app/$(TARGET): src/$(SOURCE)
	docker build -t cross-rpi .
	docker run -it --rm -d --name cross cross-rpi /bin/bash
	docker cp src cross:/home/idein/src
	docker exec -it cross bash -c '$${TARGET_TRIPLET}-gcc -W -Wall -Wextra -Werror -O2 -pipe -fPIC -std=c99 -I $${PKG_CONFIG_SYSROOT_DIR}/usr/include -I src src/$(SOURCE) -march=armv8-a -shared -o $(TARGET) -L$${PKG_CONFIG_SYSROOT_DIR}/usr/lib -lhailort -lpthread'
	docker cp cross:/home/idein/$(TARGET) app/$(TARGET)
	docker stop cross

.PHONY: clean
clean:
	rm -f app/$(TARGET)
