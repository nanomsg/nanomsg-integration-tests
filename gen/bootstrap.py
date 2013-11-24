#!/usr/bin/python
from __future__ import print_function

import re
import yaml
import shutil
import os
import os.path
import stat
import argparse
import subprocess
import sys
import shlex
import random
from string import Template
from collections import defaultdict
from itertools import count


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
        cfg.vm.network "public_network", {{
            bridge: "vagrantbr0",
            mac: '{mac}',
            }}
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

WAIT_FOR_CODE = """
start on remote-filesystems
pre-start script
    while [ ! -e /code/README.rst ]; do
        sleep 1
    done
end script
"""

IPTABLES = """
*filter
:INPUT ACCEPT [350:23648]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [389:29796]
:test-chain - [0:0]
-A INPUT -j test-chain
COMMIT
# Completed on Fri Nov 22 15:30:52 2013
"""

def updated(a, *b):
    res = a.copy()
    for i in b:
        res.update(i)
    return res


def mkupstart(prov, cfgdir, name, run, env={}):
    with open(cfgdir + '/' + name + '.conf', 'wt') as file:
        for k, v in env.items():
            print('env {}={}'.format(k, v), file=file)
        print('env NN_APPLICATION_NAME={}'.format(name), file=file)
        print('respawn', file=file)
        print('start on started wait_for_code', file=file)
        cline = ' '.join(map(shlex.quote, run.split()))
        print('exec {}'.format(cline), file=file)

    print('install -D /vagrant/{}/{}.conf /etc/init/{}.conf'
        .format(cfgdir, name, name), file=prov)
    print('service {} start'.format(name), file=prov)


def ask(*args):
    sub = subprocess.Popen(args, stdout=subprocess.PIPE)
    stdout, _ = sub.communicate()
    if sub.poll():
        print("Error running: {}".format(args))
        sys.exit(1)
    return stdout.decode('ascii')


def run(*args):
    sub = subprocess.Popen(args)
    stdout, _ = sub.communicate()
    if sub.wait():
        print("Error running: {}".format(args))
        sys.exit(1)


def add_graph(bash, html, rdir, title, graphs):
    col = set(GRAPH_COLORS)
    gname = re.sub('[^a-z_0-9]+', '-', title.strip().lower())
    print('rrdtool graph $timerange {rdir}/{gname}.png '
        .format(rdir=rdir, gname=gname) + ' '.join(graphs),
        file=bash)
    print('<h2>{title}</h2>\n'
          '<p><img src="../{rdir}/{gname}.png"></p>\n'
          .format(rdir=rdir, title=title, gname=gname),
          file=html)


class Tag(object):
    def __init__(self, tag, data):
        self.tag = tag
        self.data = data

yaml.add_representer(Tag,
    lambda dumper, t: dumper.represent_mapping(t.tag, t.data),
    Dumper=yaml.SafeDumper)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    topt, _ = ap.parse_known_args()


    with open(topt.config, 'rb') as f:
        config = yaml.safe_load(f)

    ap.add_argument('test_name', choices=config['tests'].keys())
    options = ap.parse_args()

    topologies = config['topologies']
    services = config['services']
    nodes = set(services)
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

        for nname in nodes:
            num = test.get('instances', {}).get(nname, 1)
            if num > 1:
                inames = [nname + str(i) for i in range(num)]
            else:
                inames = [nname]
            for iname in inames:
                # TODO(tailhook) implement more networking options

                print(VAGRANT_HOST.format(
                    name=iname,
                    mac='00163e{:06x}'.format(
                        random.randint(0x000000, 0xffffff)),
                    ), file=f)

            namenodes[nname] = inames
            for n in inames:
                node2name[n] = nname

        print("end", file=f)

    ipnodes = set(('master',))
    for name, lst in config['layouts'].items():
        for val in lst:
            bnode = re.match('^\s*(\w+)\s*(--|->|<-)\s*(\w+)\s*$', val
                             ).group(1)
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
        data = ask('vagrant', 'ssh', node, '--',
            'ip', 'addr', 'show', 'eth1')
        ip = re.search('inet ([\d\.]+)', data).group(1)
        name = node2name[node]
        role_ips[name].append(ip)
        node_ips[node] = ip
    role_ips = dict(role_ips)

    print("Got it. Now temporarily shutting down nodes")
    run('vagrant', 'halt')

    master_ip = node_ips['master']

    print("Generating configs")
    for node, name in node2name.items():
        nsvc = services[name]
        role = name
        ip = node_ips.get(node)
        if ip is not None:
            suffix = '?role={}&ip={}'.format(role, ip)
        else:
            suffix = '?role={}'.format(role)
        env = {
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

            with open(cfgdir + '/iptables.rules', 'wt') as wcfg:
                print(IPTABLES, file=wcfg)
                print('install -D /vagrant/{cfgdir}/iptables.rules '
                      '/etc/iptables/rules.v4'
                      .format(cfgdir=cfgdir), file=prov)
                print('update-rc.d iptables-persistent enable', file=prov)
                print('/etc/init.d/iptables-persistent start', file=prov)

            with open(cfgdir + '/wait_for_code.conf', 'wt') as wcfg:
                print(WAIT_FOR_CODE, file=wcfg)
                print('install -D /vagrant/{cfgdir}/wait_for_code.conf '
                      '/etc/init/wait_for_code.conf'
                      .format(cfgdir=cfgdir), file=prov)
                print('service wait_for_code start', file=prov)

            with open(cfgdir + '/collectd.conf', 'wt') as cfile:
                if node == 'master':
                    ctext = COLLECTD_MASTER
                else:
                    ctext = COLLECTD_SLAVE
                print(ctext.format(
                    name=node,
                    master_ip=master_ip,
                    ), file=cfile)
            print('install -D /vagrant/{cfgdir}/collectd.conf /etc/collectd/collectd.conf'
                .format(cfgdir=cfgdir), file=prov)
            print('/etc/init.d/collectd start', file=prov)

            if name == 'master':
                ports = count(20000)
                tdata = {
                    'server': {
                        'config-addr': ['tcp://{}:10000'.format(master_ip)],
                        },
                    'layouts': config['layouts'],
                    'topologies': {
                        k: Tag('!Topology', updated(v, {
                            'port': next(ports),
                            'ip-addresses': role_ips,
                        })) for k, v in topologies.items()},
                    }
                with open(cfgdir + '/topologist.yaml', 'wt') as f:
                    yaml.safe_dump(tdata, f, default_flow_style=False)
                print('install -D /vagrant/{cfgdir}/topologist.yaml /etc/topologist.yaml'
                    .format(cfgdir=cfgdir), file=prov)
                mkupstart(prov, cfgdir, 'topologist',
                    '/usr/bin/topologist', env=env)

            vars = test.get('vars', {}).copy()
            for t in topologies:
                vars['URL_' + t.upper()] = 'nanoconfig://' + t + suffix
            for sname, scli in nsvc.items():
                exestr =  Template(scli).substitute(vars)
                mkupstart(prov, cfgdir, sname, exestr, env=env)

    print("Generating timeline script")
    with open("./runtest.sh", "wt") as f:
        print("#!/usr/bin/env bash", file=f)
        print("date +%s > .test_start", file=f)
        print("start=$(<.test_start)", file=f)
        print("wait_until() { sleep $(($1 - ($(date +%s) - start)));}", file=f)
        print("echo Test started at $(date -d@$start)", file=f)
        for tm in sorted(test.get('timeline', ())):
            commands = test['timeline'][tm]
            for c in commands:
                print("wait_until {}".format(tm), file=f)
                vars = {'PORT_' + tk.upper(): tv.data['port']
                        for tk, tv in tdata['topologies'].items()}
                exestr =  Template(c['exec']).substitute(vars)
                print("vagrant ssh {} -c {}"
                    .format(c['node'], shlex.quote(exestr)), file=f)

        print("wait_until {}".format(test['duration']), file=f)
        print("date +%s > .test_finish", file=f)
        print("echo Test finished at $(date -d@$(<.test_finish))", file=f)
        print('rsync --archive --stats '
              '--rsh="vagrant ssh master -- exec -a" '
              'master:/var/lib/collectd/ rrd', file=f)
        print("echo Done, now run ./mkreport.sh\n", file=f)

    print("Generating report script")
    rdir = 'report/' + options.test_name
    if not os.path.exists(rdir):
        os.makedirs(rdir)
    with open("./mkreport.sh", "wt") as f, \
         open(rdir + ".html", "wt") as h:

        print("#!/usr/bin/env bash", file=f)
        print("rm "+rdir, file=f)
        print('timerange="--start $(<.test_start) --end $(<.test_finish)"', file=f)

        print('<!DOCTYPE html>', file=h)
        print('<html><head>', file=h)
        print('<title>Test report: {}</title>'.format(options.test_name), file=h)
        print('</head><body>', file=h)
        print('<h1>Test report: {}</h1>'.format(options.test_name), file=h)

        col = set(GRAPH_COLORS)
        add_graph(f, h, rdir, 'Load Averages', [
            'DEF:{name}=rrd/{name}/load/load.rrd:shortterm:AVERAGE '
            'LINE1:{name}{color}:{name}'.format(name=name, color=col.pop())
            for name in node2name])

        for gtitle, g in config.get('graphs', {}).items():
            add_graph(f, h, rdir, gtitle, [
                'DEF:{name}=rrd/{name}/{def} LINE1:{name}{color}:{name}'
                .format(name=name, color=col.pop(), **g)
                for name in namenodes[g['role']] ])

        print('</body></html>', file=h)

    st = os.stat('./runtest.sh')
    os.chmod('./runtest.sh', st.st_mode | stat.S_IEXEC)
    st = os.stat('./mkreport.sh')
    os.chmod('./mkreport.sh', st.st_mode | stat.S_IEXEC)

    print("Now to run test, execute the following:")
    print("    vagrant up --provision")
    print("    ./runtest.sh")
    print("    vagrant destroy --force")
    print("    ./mkreport.sh")


if __name__ == '__main__':
    main()
