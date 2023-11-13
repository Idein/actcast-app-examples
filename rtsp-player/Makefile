.PHONY: all
all: app/bin/tcp2socksd

app/bin/tcp2socksd:
	curl -OL https://github.com/Idein/tcp2socks/releases/download/0.1.1/tcp2socksd-0.1.1-arm-unknown-linux-gnueabihf.tar.gz
	tar -xf tcp2socksd-0.1.1-arm-unknown-linux-gnueabihf.tar.gz
	mkdir -p app/bin
	mv tcp2socksd-0.1.1-arm-unknown-linux-gnueabihf/tcp2socksd app/bin/
	rm -rf tcp2socksd-0.1.1-arm-unknown-linux-gnueabihf*

.PHONY: clean
clean:
	rm -rf app/bin
