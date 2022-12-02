VUTILS = vutils.pl
VUTILSDEST = /usr/local/bin/vutils.pl
VRM = /usr/local/bin/vrm
VSTAT = /usr/local/bin/vstat
VEXTRACT = /usr/local/bin/vextract
VREVERT = /usr/local/bin/vrevert

MOUNTPROG = mount.wayback
MOUNTDEST = /bin/mount.wayback

INSTALL = /usr/bin/install
INSTALLMOUNT = $(INSTALL) -o root -m 4755

all: wayback


wayback:
	make -C src

install: waybackinstall mountinstall utilinstall

waybackinstall:
	$(INSTALL) ./src/wayback /usr/local/bin/wayback

mountinstall:
	$(INSTALLMOUNT) $(MOUNTPROG) $(MOUNTDEST)

utilinstall: vutilsinstall vrminstall vstatinstall vextractinstall vrevertinstall

vutilsinstall:
	$(INSTALL) $(VUTILS) $(VUTILSDEST)

vrminstall:
	ln -s $(VUTILSDEST) $(VRM)

vstatinstall:
	ln -s $(VUTILSDEST) $(VSTAT)

vextractinstall:
	ln -s $(VUTILSDEST) $(VEXTRACT)

vrevertinstall:
	ln -s $(VUTILSDEST) $(VREVERT)

clean:
	make -C src clean
