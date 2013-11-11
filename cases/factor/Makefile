# VM settings
NWORKERS?=3
BRIDGE?=br0

# Testrun settings
NREQUESTS?=10000

test: config vboxes load

load:
	vagrant ssh master -- python2 /code/checkfactor.py --requests $(NREQUESTS)

vboxes_up:
	vagrant up --no-provision

vboxes_prepare_configs: vboxes_up
	-mkdir tmpcfg
	(\
		master_ip=$$(vagrant ssh master -- ip -f inet addr show eth1 | grep -Po 'inet \K[\.\d]+'); \
		sed 's/@master:ip@/'$$master_ip'/' < vm/factor.conf > tmpcfg/factor.conf; \
	 	sed 's/@master:ip@/'$$master_ip'/' < vm/topologist.yaml > tmpcfg/topologist.yaml; \
	)

vboxes_configure: vboxes_prepare_configs
	vagrant reload --provision

vboxes: vboxes_configure

config: Vagrantfile

Vagrantfile: vm/vagrant.tpl
	sed \
		's/@num_workers@/$(NWORKERS)/' \
		's/@bridge@/$(BRIDGE)/' \
		vm/vagrant.tpl > $@

clean:
	vagrant destroy --force
	rm Vagrantfile

.PHONY: test config clean vboxes load vboxes_up vboxes_prepare_configs vboxes_configure
