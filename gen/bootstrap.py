#!/usr/bin/python
from __future__ import print_function

import re
import yaml
import shutil
import os.path
import argparse
import subprocess
import sys
from collections import defaultdict


VAGRANT_HEAD = """
    Vagrant.configure("2") do |config|
        config.vm.box = "nntest"
        config.vm.box_url = "../../projects/nntest.box"
        config.vm.synced_folder "../../code", "/code"
"""

VAGRANT_HOST = """
    config.vm.define "{name}" do |cfg|
        cfg.vm.provision "shell", path: '_provision/scripts/{name}.sh'
        cfg.vm.network "public_network", :bridge => "br0"
    end
"""

COLLECTD_MASTER = """
    Hostname    "{name}"
    BaseDir     "/var/lib/collectd"
    PIDFile     "/run/collectd.pid"
    PluginDir   "/usr/lib/collectd"
    TypesDB     "/usr/share/collectd/types.db"

    LoadPlugin syslog
    LoadPlugin cpu
    LoadPlugin interface
    LoadPlugin load
    LoadPlugin memory
    LoadPlugin rrdtool
    LoadPlugin nanomsg_estp

    <Plugin "nanomsg_estp">
      <Socket Subscribe>
        Bind "tcp://{master_ip}:10001"
      </Socket>
    </Plugin>
"""

COLLECTD_SLAVE = """
    Hostname    "{name}"
    BaseDir     "/tmp"
    PIDFile     "/run/collectd.pid"
    PluginDir   "/usr/lib/collectd"
    TypesDB     "/usr/share/collectd/types.db"

    LoadPlugin syslog
    LoadPlugin cpu
    LoadPlugin interface
    LoadPlugin load
    LoadPlugin memory
    LoadPlugin nanomsg_estp

    <Plugin "nanomsg_estp">
      <Socket Publish>
        Connect "tcp://{master_ip}:10001"
      </Socket>
    </Plugin>
"""


def mkupstart(prov, cfgdir, name, run, env={}):
    with open(cfgdir + '/' + name + '.conf', 'rt') as f:
        for k, v in env.items():
            print('env {}={}'.format(k, v), file=file)
        print('respawn', file=file)
        print('start on mounted', file=file)
        print('exec {}'.format(run), file=file)

    print('install {}/{}.conf /etc/init/{}.conf'.format(cfgdir, name, name),
        file=prov)
    print('service {} start'.format(name), file=prov)


def run(*args):
    sub = subprocess.Popen(args, stdout=subprocess.PIPE)
    stdout, _ = sub.communicate()
    if sub.poll():
        print("Error running: {}".format(args))
        sys.exit(1)
    return stdout.decode('ascii')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    topt, _ = ap.parse_known_args()


    with open(topt.config, 'rb') as f:
        data = yaml.load(f)

    ap.add_argument('test_name', choices=data['tests'].keys())
    options = ap.parse_args()

    nodes = data['nodes']
    test = data['tests'][options.test_name]

    print("Cleaning old configuration")
    if os.path.exists('_provision'):
        shutil.rmtree('_provision')
    if os.path.exists('Vagrantfile'):
        os.unlink('Vagrantfile')

    print("Preparing vagrant configuration")
    os.makedirs('_provision')
    os.makedirs('_provision/scripts')
    os.makedirs('_provision/cfg')

    role2name = {}
    name2role = {}
    with open('Vagrantfile', 'wt') as f:
        print(VAGRANT_HEAD, file=f)

        for nname, nprops in nodes.items():
            num = test.get('instances', {}).get(nname, 1)
            if num > 1:
                inames = [nname + str(i) for i in range(num)]
            else:
                inames = [nname]
            for iname in inames:
                # TODO(tailhook) implement more networking options
                print(VAGRANT_HOST.format(name=iname), file=f)

            role2name[nname] = inames
            for n in inames:
                name2role[n] = nname

        print("end", file=f)

    node_ips = set(('master',))
    for val in data['layout']:
        bnode = re.match('^\s*(\w+)\s*(--|->|<-)\s*(\w+)\s*$', val).group(0)
        node_ips.add(bnode)

    print("Starting up {} to get their ip addresses"
        .format(', '.join(node_ips)))
    run('vagrant', 'up', '--no-provision', *node_ips)

    role_ips = defaultdict(list)
    node_ips = {}
    for node in node_ips:
        # TODO(tailhook) check if other network interface may be used
        data = run('vagrant', 'ssh', node, '--',
            'ip', 'addr', 'show', 'eth1')
        ip = re.find('inet ([\d\.]+)').group(0)
        role_ips[name2role[node]].append(ip)
        node_ips[node] = ip

    print("Got it. Now temporarily shutting down nodes")
    run('vagrant', 'halt')

    master_ip, = node_ips['master']

    print("Generating configs")
    for name, role in name2role.items():
        ip = node_ips.get(name)
        if ip is not None:
            url = 'nanoconfig://default?role={}&ip={}'.format(role, ip)
        else:
            url = 'nanoconfig://default?role={}'.format(role)
        env = {
            'TOPOLOGY_URL': url,
            'NN_CONFIG_SERVICE': 'tcp://{}:10000'.format(master_ip),
            'NN_PRINT_ERRORS': '1',
            'NN_STATISTICS_SOCKET': 'tcp://{}:10001'.format(master_ip),
            }

        cfgdir = '_provision/cfg/' + name
        os.mkdir(cfgdir)

        with open('_provision/scripts/' + name + '.sh', 'wt') as prov:
            print('#!/usr/bin/env bash', file=prov)
            print('echo {} > /etc/hostname'.format(name), file=prov)
            print('hostname {}'.format(name), file=prov)

            # Every node
            with open(cfgdir + '/collectd.conf', 'wt') as cfile:
                if node == 'master':
                    ctext = COLLECTD_MASTER
                else:
                    ctext = COLLECTD_SLAVE
                print(ctext.format(
                    name=name,
                    master_ip = node_ips['master'][0],
                    ), file=cfile)
            print('install {cfgdir}/collectd.conf /etc/collectd/collectd.conf'
                .format(cfgdir=cfgdir), file=prov)
            print('/etc/init.d/collectd start', file=prov)

            if name == 'master':
                tdata = {
                    'layouts': {'default': data['layout']},
                    'topologies': {
                        'default': {
                            'type': 'reqrep',
                            'layout': 'default',
                            'default-port': 20000,
                            'ip_addresses': role_ips,
                    }}}
                with open(cfgdir + '/topologist.yaml', 'wt') as f:
                    yaml.dump(tdata, f)
                print('install {cfgdir}/topologist.yaml /etc/topologist.yaml'
                    .format(cfgdir=cfgdir), file=prov)
                mkupstart(prov, cfgdir, 'topolotist',
                    '/usr/bin/topologist', env=env)





if __name__ == '__main__':
    main()
