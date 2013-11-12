DESTDIR:=$(PWD)/_dist
CFLAGS:="-I$(DESTDIR)/usr/include"
LDFLAGS:="-L$(DESTDIR)/usr/lib"
PROVIDER?="virtualbox"

all: nanomsg nanoconfig topologist nanomsg-python collectd-nanomsg-estp

box: nntest.box

clean: nanomsg_clean nanoconfig_clean topologist_clean
clean: nanomsg-python_clean collectd-nanomsg-estp_clean
clean:
	-rm -rf _build _dist

boxclean:
	-rm -rf nntest.box


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
	cd _build/nanoconfig; cmake ../../nanoconfig \
		-DCMAKE_INSTALL_PREFIX=/usr \
		-DCMAKE_C_FLAGS=$(CFLAGS) \
		-DCMAKE_SHARED_LINKER_FLAGS=$(LDFLAGS) -DCMAKE_EXE_LINKER_FLAGS=$(LDFLAGS)
	make -C _build/nanoconfig install DESTDIR=$(DESTDIR)

nanoconfig_clean:
	# nothing, all artifacts in the build directory

topologist:
	-mkdir -p _build/topologist
	cd _build/topologist; cmake ../../topologist \
		-DCMAKE_INSTALL_PREFIX=/usr -DASTYLE= \
		-DCMAKE_C_FLAGS=$(CFLAGS) -DCMAKE_EXE_LINKER_FLAGS=$(LDFLAGS)
	make -C _build/topologist install DESTDIR=$(DESTDIR)

topologist_clean:
	# nothing, all artifacts in the build directory

nanomsg-python: nanoconfig
	cd nanomsg-python; LD_LIBRARY_PATH=$(DESTDIR)/usr/lib python setup.py build_ext $(CFLAGS) $(LDFLAGS)
	cd nanomsg-python; python setup.py install --root=$(DESTDIR)/ --optimize=1

nanomsg-python_clean:
	rm -rf nanomsg-python/build

collectd-nanomsg-estp:
	make -C collectd-nanomsg-estp install DESTDIR=$(DESTDIR) CFLAGS=$(CFLAGS) LDFLAGS=$(LDFLAGS)

collectd-nanomsg-estp_clean:
	make -C collectd-nanomsg-estp clean

nntest.box:
	make clean
	vagrant destroy --force builder boxer
	vagrant up builder --provider=$(PROVIDER)
	vagrant destroy --force builder
	vagrant up boxer --provider=$(PROVIDER)
	vagrant package boxer --output $@
	vagrant destroy --force boxer



.PHONY: all nanomsg nanoconfig topologist nanomsg-python collectd-nanomsg-estp
.PHONY: clean nanomsg_clean nanoconfig_clean topologist_clean
.PHONY: nanomsg-python_clean collectd-nanomsg-estp_clean
.PHONY: box
