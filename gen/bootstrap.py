#!/usr/bin/python
from __future__ import print_function

import re
import yaml
import shutil
import os.path
import argparse
import subprocess
import sys
import shlex
from collections import defaultdict

GRAPH_COLORS = {
    '#8a56e2',
    '#cf56e2',
    '#e256ae',
    '#e25668',
    '#e28956',
    '#e2cf56',
    '#aee256',
    '#68e256',
    '#56e289',
    '#56e2cf',
    '#56aee2',
    '#5668e2',
    }

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
    with open(cfgdir + '/' + name + '.conf', 'wt') as file:
        for k, v in env.items():
            print('env {}={}'.format(k, v), file=file)
        print('respawn', file=file)
        print('start on mounted', file=file)
        print('exec {}'.format(run), file=file)

    print('install /vagrant/{}/{}.conf /etc/init/{}.conf'
        .format(cfgdir, name, name), file=prov)
    print('service {} start'.format(name), file=prov)


def run(*args):
    sub = subprocess.Popen(args, stdout=subprocess.PIPE)
    stdout, _ = sub.communicate()
    if sub.poll():
        print("Error running: {}".format(args))
        sys.exit(1)
    return stdout.decode('ascii')

def add_graph(bash, html, title, values):
    graphs = []
    col = set(GRAPH_COLORS)
    for name, val in values.items():
        line = val.format(name=name, color=col.pop())
        graphs.append(line)
    gname = re.sub('[^a-z_0-9]+', '-', title.strip().lower())
    print('rrdtool graph $timerange report/{gname}.png' + ' '.join(graphs),
        file=bash)
    print('<h2>{title}</h2>\n'
          '<p><img src="{gname}.png"></p>\n'
          .format(title=title, gname=gname),
          file=html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    topt, _ = ap.parse_known_args()


    with open(topt.config, 'rb') as f:
        config = yaml.safe_load(f)

    ap.add_argument('test_name', choices=config['tests'].keys())
    options = ap.parse_args()

    nodes = config['nodes']
    test = config['tests'][options.test_name]

    print("Cleaning old configuration")
    if os.path.exists('_provision'):
        shutil.rmtree('_provision')
    if os.path.exists('Vagrantfile'):
        os.unlink('Vagrantfile')

    print("Preparing vagrant configuration")
    os.makedirs('_provision')
    os.makedirs('_provision/scripts')
    os.makedirs('_provision/cfg')

    namenodes = {}
    node2name = {}
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

            namenodes[nname] = inames
            for n in inames:
                node2name[n] = nname

        print("end", file=f)

    ipnodes = set(('master',))
    for val in config['layout']:
        bnode = re.match('^\s*(\w+)\s*(--|->|<-)\s*(\w+)\s*$', val).group(1)
        ipnodes.add(bnode)

    print("Starting up [{}] to get their ip addresses"
        .format(', '.join(ipnodes)))
    for n in ipnodes:
        #  Creating stub provisioning scripts so that vagrant be happy
        with open('_provision/scripts/' + n + '.sh', 'wt') as f:
            pass
    run('vagrant', 'up', '--no-provision', *ipnodes)

    role_ips = defaultdict(list)
    node_ips = {}
    for node in ipnodes:
        # TODO(tailhook) check if other network interface may be used
        data = run('vagrant', 'ssh', node, '--',
            'ip', 'addr', 'show', 'eth1')
        ip = re.search('inet ([\d\.]+)', data).group(1)
        name = node2name[node]
        role = nodes.get(name, {}).get('role', name)
        role_ips[role].append(ip)
        node_ips[node] = ip
    role_ips = dict(role_ips)

    print("Got it. Now temporarily shutting down nodes")
    run('vagrant', 'halt')

    master_ip = node_ips['master']

    print("Generating configs")
    for node, name in node2name.items():
        props = nodes.get(name, {})
        role = props.get('role', name)
        ip = node_ips.get(node)
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

        cfgdir = '_provision/cfg/' + node
        os.mkdir(cfgdir)

        with open('_provision/scripts/' + node + '.sh', 'wt') as prov:
            print('#!/usr/bin/env bash', file=prov)
            print('echo {} > /etc/hostname'.format(name), file=prov)
            print('hostname {}'.format(node), file=prov)

            # Every node
            with open(cfgdir + '/collectd.conf', 'wt') as cfile:
                if node == 'master':
                    ctext = COLLECTD_MASTER
                else:
                    ctext = COLLECTD_SLAVE
                print(ctext.format(
                    name=node,
                    master_ip=master_ip,
                    ), file=cfile)
            print('install /vagrant/{cfgdir}/collectd.conf /etc/collectd/collectd.conf'
                .format(cfgdir=cfgdir), file=prov)
            print('/etc/init.d/collectd start', file=prov)

            if name == 'master':
                tdata = {
                    'layouts': {'default': config['layout']},
                    'topologies': {
                        'default': {
                            'type': 'reqrep',
                            'layout': 'default',
                            'default-port': 20000,
                            'ip_addresses': role_ips,
                    }}}
                with open(cfgdir + '/topologist.yaml', 'wt') as f:
                    yaml.safe_dump(tdata, f, default_flow_style=False)
                print('install /vagrant/{cfgdir}/topologist.yaml /etc/topologist.yaml'
                    .format(cfgdir=cfgdir), file=prov)
                mkupstart(prov, cfgdir, 'topologist',
                    '/usr/bin/topologist', env=env)

            if 'run' in props:
                vars = test.get('vars', {}).copy()
                vars['TOPOLOGY_URL'] = url
                exestr = re.sub('\$(\w+)',
                    lambda m: str(test['vars'].get(m.group(1))),
                    props['run'])
                mkupstart(prov, cfgdir, role, exestr, env=env)

    print("Generating timeline script")
    with open("./runtest.sh", "wt") as f:
        print("#!/usr/bin/env bash", file=f)
        print("date +%s > .test_start", file=f)
        print("start=$(<.test_start)", file=f)
        print("echo Test started at $(date -d@$start)", file=f)
        for tm in sorted(test.get('timeline', ())):
            commands = test['timeline'][tm]
            for c in commands:
                print("sleep $(({} - ($(date +%s) - start)))"
                    .format(tm), file=f)
                print("vagrant ssh {} -c {}"
                    .format(c['node'], shlex.quote(c['exec'])), file=f)

        print("sleep $(({} - ($(date +%s) - start)))"
            .format(test['duration']), file=f)
        print("date +%s > .test_finish", file=f)
        print("echo Test finished at $(date -d@$(<.test_finish))", file=f)
        print('rsync --archive --stats '
              '--rsh="vagrant ssh master -- exec -a" '
              'master:/var/lib/collectd/ rrd', file=f)
        print("echo Done, now run ./mkreport.sh\n", file=f)

    print("Generating report script")
    if not os.path.exists('report'):
        os.mkdir('report')
    with open("./mkreport.sh", "wt") as f, \
         open("./report/all_graphs.html", "wt") as h:

        print("#!/usr/bin/env bash", file=f)
        print("rm report/*.png", file=f)
        print('timerange="--start $(<time_start) --end $(<time_finish)', file=f)

        print('<!DOCTYPE html>', file=h)
        print('<html><head>', file=h)
        print('<title>Test report: {}</title>'.format(options.test_name), file=h)
        print('</head><body>', file=h)
        print('<h1>Test report: {}</h1>'.format(options.test_name), file=h)

        add_graph(f, h, 'Load Averages', {node:
            'DEF:{name}=rrd/{name}/load/load.rrd:shortterm:AVERAGE LINE1:{name}{color}:{name}'
            for node in node2name})

        print('</body></html>', file=h)

    print("Now to run test, execute the following:")
    print("    vagrant up --provision")
    print("    ./runtest.sh")
    print("    vagrant destroy --force")
    print("    ./mkreport.sh")


if __name__ == '__main__':
    main()
