#!/usr/bin/env bash
install /vagrant/tmpcfg/topologist.yaml /etc/topologist.yaml
install /vagrant/tmpcfg/factor.conf /etc/init/factor.conf
service factor start
