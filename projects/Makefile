DESTDIR:=$(PWD)/_dist

all: nanomsg nanoconfig topologist nanomsg-python collectd-nanomsg-estp

clean: nanomsg_clean nanoconfig_clean topologist_clean
clean: nanomsg-python_clean collectd-nanomsg-estp_clean
clean:
	rm -rf _build _dist


nanomsg:
	-mkdir -p _build/nanomsg
	cd nanomsg; sh autogen.sh
	cd _build/nanomsg; ../../nanomsg/configure --prefix=/usr
	make -C _build/nanomsg
	make -C _build/nanomsg install DESTDIR=$(DESTDIR)

nanomsg_clean:
	git clean -fdX nanomsg  # any better way of cleaning autogen?

nanoconfig:
	-mkdir -p _build/nanoconfig
	cd _build/nanoconfig; cmake ../../nanoconfig -DCMAKE_INSTALL_PREFIX=/usr
	make -C _build/nanoconfig install DESTDIR=$(DESTDIR)

nanoconfig_clean:
	# nothing, all artifacts in the build directory

topologist:
	-mkdir -p _build/topologist
	cd _build/topologist; cmake ../../topologist -DCMAKE_INSTALL_PREFIX=/usr -DASTYLE=
	make -C _build/topologist install DESTDIR=$(DESTDIR)

topologist_clean:
	# nothing, all artifacts in the build directory

nanomsg-python:
	cd nanomsg-python; python setup.py install --root=$(DESTDIR)/ --optimize=1

nanomsg-python_clean:
	rm -rf nanomsg-python/build

collectd-nanomsg-estp:
	make -C collectd-nanomsg-estp install DESTDIR=$(DESTDIR)

collectd-nanomsg-estp_clean:
	make -C collectd-nanomsg-estp clean


.PHONY: all nanomsg nanoconfig topologist nanomsg-python collectd-nanomsg-estp
.PHONY: clean nanomsg_clean nanoconfig_clean topologist_clean
.PHONY: nanomsg-python_clean collectd-nanomsg-estp_clean
