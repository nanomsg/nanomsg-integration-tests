# VM settings
NWORKERS?=3
BRIDGE?=br0

# Testrun settings
NREQUESTS?=10000


test: config vboxes load report

load:
	@date +%s > tmpcfg/start_timestamp
	@echo Test started at $(shell date -d@$(shell cat tmpcfg/start_timestamp))
	vagrant ssh master -- "/vagrant/tmpcfg/loadscript.sh" $(NREQUESTS)
	@date +%s > tmpcfg/finish_timestamp
	@echo Test finished at $(shell date -d@$(shell cat tmpcfg/finish_timestamp))
	@echo Downloading RRDs
	rsync --archive --stats --rsh="vagrant ssh master -- exec -a" master:/var/lib/collectd/ rrd


report: tmpcfg/start_timestamp tmpcfg/finish_timestamp
	-mkdir report
	./graphs.sh $(NWORKERS)

vboxes_up:
	vagrant up --no-provision

configure: vboxes_up
	-mkdir tmpcfg
	master_ip=$$(vagrant ssh master -- ip -f inet addr show eth1 | grep -Po 'inet \K[\.\d]+'); \
	sed 's/@master:ip@/'$$master_ip'/g' < vm/factor.conf > tmpcfg/factor.conf; \
	sed 's/@master:ip@/'$$master_ip'/g' < vm/topologist.yaml > tmpcfg/topologist.yaml; \
	sed 's/@master:ip@/'$$master_ip'/g' < vm/topologist.conf > tmpcfg/topologist.conf; \
	sed 's/@master:ip@/'$$master_ip'/g' < vm/loadscript.sh > tmpcfg/loadscript.sh; \
	MASTER_IP=$$master_ip vagrant reload --provision
	chmod +x tmpcfg/loadscript.sh


vboxes: configure

config: Vagrantfile

Vagrantfile: vm/vagrant.tpl
	sed \
		's/@num_workers@/$(NWORKERS)/g;s/@bridge@/$(BRIDGE)/g' \
		vm/vagrant.tpl > $@

clean:
	vagrant destroy --force
	rm Vagrantfile
	rm -rf rrd

.PHONY: test config clean vboxes load vboxes_up vboxes_prepare_configs vboxes_configure report
