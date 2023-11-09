.PHONY: all
all: app/libmodel.so app/model.py include/model.h

app/libmodel.so app/model.py include/model.h:
	actdk compile

.PHONY: clean
clean:
	rm -f app/*.so
	rm -f app/model.py
	rm -f include/model.h
