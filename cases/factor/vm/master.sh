#!/usr/bin/env bash
install /vagrant/tmpcfg/topologist.yaml /etc/topologist.yaml
install /vagrant/tmpcfg/topologist.conf /etc/init/topologist.conf
install /vagrant/vm/master_collectd.conf /etc/collectd/collectd.conf
/etc/init.d/collectd start
service topologist start
