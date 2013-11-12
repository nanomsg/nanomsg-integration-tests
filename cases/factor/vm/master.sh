#!/usr/bin/env bash
install /vagrant/tmpcfg/topologist.yaml /etc/topologist.yaml
install /vagrant/vm/topologist.conf /etc/init/topologist.conf
service topologist start
