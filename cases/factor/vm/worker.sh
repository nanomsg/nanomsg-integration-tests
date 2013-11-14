#!/usr/bin/env bash
name="$1"
master_ip="$2"
echo "$name" > /etc/hostname
hostname "$name"
install /vagrant/tmpcfg/factor.conf /etc/init/factor.conf
sed 's/@machine:name@/'$name'/g;s/@master:ip@/'$master_ip'/g' < /vagrant/vm/worker_collectd.conf > /etc/collectd/collectd.conf
/etc/init.d/collectd start
service factor start

