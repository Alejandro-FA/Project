#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Host, Node
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.util import irange
from util import Network

def NATNetwork(nrouters=2, nhosts=3, server=False):
    """nrouters: number of local subnets to build (each one has 1 router)
       nhosts: number of hosts per local subnet"""
    netN = Network('172.16.0.0/16')
    netR = Network('10.10.10.0/24')
    netH = Network('192.168.0.0/16', nextSubnet='192.168.1.0')

    net = Mininet(ipBase=netN.ip)

    info( '*** Adding switches\n')
    for i in irange(0, nrouters):
        net.addSwitch('s%d' % i, cls=OVSKernelSwitch, failMode='standalone')

    info( '*** Adding NAT\n')
    nat = net.addNAT('nat', connect=None, ip=netN.giveIP('nat'), flush=True)
    net.addLink(net.get('s0'), nat, port2=0)

    info( '*** Adding routers\n')
    for i in irange(1, nrouters):
        subnet = netH.addSubnet(minHosts=max(254, nhosts))
        r = net.addHost('r%d' % i, cls=Node, ip=None)
        net.addLink(net.get('s0'), r, params2={'ip':netN.giveIP(r.name)}, port2=0)
        net.addLink(net.get('s%d'%i), r, params2={'ip':subnet.giveIP(r.name)}, port2=i)

    # Connect all routers between them in a mesh topology
    for i in irange(1, nrouters):
        for j in irange(i+1, nrouters):
            subnet = netR.addSubnet(minHosts=2)
            net.addLink(net.get('r%d'%i), net.get('r%d'%j),
                params1={'ip':subnet.giveIP('r%d'%i)}, port1=j,
                params2={'ip':subnet.giveIP('r%d'%j)}, port2=i)

    info( '*** Adding hosts\n')
    n = 0
    for i in irange(1, nrouters):
        for j in irange(1, nhosts):
            n += 1
            h = net.addHost('h%d'%n, cls=Host, ip=netH.subnets[i-1].giveIP('h%d'%n))
            net.addLink(h, net.get('s%d'%i), port1=0)

    info( '*** Topology created:\n')
    netN.show()
    netR.show()
    netH.show()

    info( '*** Starting network\n')
    net.start()

    info('*** Configuring default routes\n')
    n = 0
    for i in irange(1, nrouters):
        r = net.get('r%d'%i)
        r.setDefaultRoute('dev ' + r.intfs[0].name + ' via ' + nat.IP())
        for j in irange(1, nhosts):
            n += 1
            h = net.get('h%d'%n)
            h.setDefaultRoute('dev '+ h.intfs[0].name+ ' via '+ r.intfs[i].IP())

    info( '*** Configuring static routes\n')
    for i in irange(1, nrouters):
        ri = net.get('r%d'%i)
        nat.cmd('ip route add ' + netH.subnets[i-1].ip + ' via ' +
                 ri.intfs[0].IP() + ' dev ' + nat.intfs[0].name)
        for j in irange(1,i-1) + irange(i+1, nrouters):
            rj = net.get('r%d'%j)
            ri.cmd('ip route add ' + netH.subnets[j-1].ip + ' via ' +
                    rj.intfs[i].IP() + ' dev ' + ri.intfs[j].name)

    info( '*** Configuring NAT rules\n')
    for subnet in netH.subnets:
        nat.cmd( 'iptables -I FORWARD','-i', nat.intfs[0], '-d', subnet.ip, '-j DROP' )
        nat.cmd( 'iptables -A FORWARD','-i', nat.intfs[0], '-s', subnet.ip, '-j ACCEPT' )
        nat.cmd( 'iptables -A FORWARD','-o', nat.intfs[0], '-d', subnet.ip, '-j ACCEPT' )
        nat.cmd( 'iptables -t nat -A POSTROUTING','-s', subnet.ip, "'!'", '-d', subnet.ip,'-j MASQUERADE' )

    if server is True:
        i = 1
        info( '*** Executing Flask server on host h%d (in the background).\n'
              '    Server output will be redirected to Flask.log\n' % i)
        net.get('h%d'%i).cmd('python Flask.py --ip', net.get('h%d'%i).IP(),
                             '> Flask.log 2>&1 &')

        info( '*** Configuring NAT to forward incoming tcp packets with\n'
              '    destination port 5200 to %s:5200\n' % net.get('h%d'%i).IP())
        nat.cmd('iptables -t nat -A PREROUTING', '-i', 'enp0s3', '-p tcp',
                '--dport 5200 -j DNAT', '--to %s:5200' % net.get('h%d'%i).IP())

    # info( "*** Testing network connectivity\n" )
    # net.pingAll()

    info( '*** Network is fully configured\n')
    CLI(net)
    info( '*** Removing NAT rules\n')
    for subnet in netH.subnets:
        nat.cmd( 'iptables -D FORWARD','-i', nat.intfs[0], '-d', subnet.ip, '-j DROP' )
        nat.cmd( 'iptables -D FORWARD','-i', nat.intfs[0], '-s', subnet.ip, '-j ACCEPT' )
        nat.cmd( 'iptables -D FORWARD','-o', nat.intfs[0], '-d', subnet.ip, '-j ACCEPT' )
        nat.cmd( 'iptables -t nat -D POSTROUTING','-s', subnet.ip, "'!'", '-d', subnet.ip,'-j MASQUERADE' )
    if server is True:
        nat.cmd('iptables -t nat -D PREROUTING', '-i', 'enp0s3', '-p tcp',
                '--dport 5200 -j DNAT', '--to %s:5200' % net.get('h%d'%i).IP())
    net.stop()

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Create Mininet Network with NAT.')
    server_flag = parser.add_mutually_exclusive_group()

    parser.add_argument("-N","--nrouters",dest="nrouters", default=2, type=int,
                        help="Number of routers to add to the topology. Default: 2")
    parser.add_argument("-n","--nhosts",dest="nhosts", default=3, type=int,
                        help="Number of hosts to add to each router. Default: 3")
    server_flag.add_argument("-s","--server",dest="flag", action='store_true',
                        help="Execute a flask server in on of the hosts")
    server_flag.add_argument("-c","--client",dest="flag", action='store_false',
                        help="Don't execute a flask server in on of the hosts")

    parser.set_defaults(flag=False)
    args = parser.parse_args()

    setLogLevel( 'info' )
    NATNetwork(nrouters=args.nrouters, nhosts=args.nhosts, server=args.flag)
