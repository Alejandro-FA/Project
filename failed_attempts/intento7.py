#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Host, Node
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def myNetwork():
    net = Mininet(ipBase='176.16.0.0/16')

    info( '*** Adding switches\n')
    s0 = net.addSwitch('s0', cls=OVSKernelSwitch, failMode='standalone')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, failMode='standalone')

    info( '*** Adding NAT\n')
    nat = net.addNAT('nat', connect=None, ip='176.16.0.1/16', flush=True)
    net.addLink(s0, nat, port2=0)

    info( '*** Adding routers\n')
    # Since we specify the IP adresses for each interface later, we have to use ip=None
    r1 = net.addHost('r1', cls=Node, ip=None)
    net.addLink(s0, r1, params2={'ip':'176.16.0.2/16'}, port2=0)
    net.addLink(s1, r1, params2={'ip':'192.168.1.1/24'}, port2=1)

    r2 = net.addHost('r2', cls=Node, ip=None)
    net.addLink(s0, r2, params2={'ip':'176.16.0.3/16'}, port2=0)
    net.addLink(s2, r2, params2={'ip':'192.168.2.1/24'}, port2=2)

    net.addLink(r1, r2, params1={'ip':'10.10.10.1/30'}, port1=2,
                        params2={'ip':'10.10.10.2/30'}, port2=1)

    info( '*** Adding hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='192.168.1.2/24')
    h2 = net.addHost('h2', cls=Host, ip='192.168.1.3/24')
    h3 = net.addHost('h3', cls=Host, ip='192.168.1.4/24')
    h4 = net.addHost('h4', cls=Host, ip='192.168.2.2/24')
    h5 = net.addHost('h5', cls=Host, ip='192.168.2.3/24')
    h6 = net.addHost('h6', cls=Host, ip='192.168.2.4/24')
    net.addLink(h1, s1, port1=0)
    net.addLink(h2, s1, port1=0)
    net.addLink(h3, s1, port1=0)
    net.addLink(h4, s2, port1=0)
    net.addLink(h5, s2, port1=0)
    net.addLink(h6, s2, port1=0)

    info( '*** Starting network\n')
    # net.build()
    net.start()

    info('*** Configuring default routes\n')
    r1.setDefaultRoute('dev ' + r1.intfs[0].name + ' via ' + nat.IP())
    r2.setDefaultRoute('dev ' + r2.intfs[0].name + ' via ' + nat.IP())

    h1.setDefaultRoute('dev ' + h1.intfs[0].name + ' via ' + r1.intfs[1].IP())
    h2.setDefaultRoute('dev ' + h2.intfs[0].name + ' via ' + r1.intfs[1].IP())
    h3.setDefaultRoute('dev ' + h3.intfs[0].name + ' via ' + r1.intfs[1].IP())
    h4.setDefaultRoute('dev ' + h4.intfs[0].name + ' via ' + r2.intfs[2].IP())
    h5.setDefaultRoute('dev ' + h5.intfs[0].name + ' via ' + r2.intfs[2].IP())
    h6.setDefaultRoute('dev ' + h6.intfs[0].name + ' via ' + r2.intfs[2].IP())

    info( '*** Configuring static routes\n')
    # 192.168.1.0/24
    r2.cmd('ip route add ' + '192.168.1.0/24' + ' via ' + r1.intfs[2].IP() + ' dev ' + r2.intfs[1].name)
    nat.cmd('ip route add ' + '192.168.1.0/24' + ' via ' + r1.intfs[0].IP() + ' dev ' + nat.intfs[0].name)
    # 192.168.2.0/24
    r1.cmd('ip route add ' + '192.168.2.0/24' + ' via ' + r2.intfs[1].IP() + ' dev ' + r1.intfs[2].name)
    nat.cmd('ip route add ' + '192.168.2.0/24' + ' via ' + r2.intfs[0].IP() + ' dev ' + nat.intfs[0].name)

    info( '*** Configuring NAT rules\n')
    for subnet in ['192.168.1.0/24', '192.168.2.0/24']:
        nat.cmd( 'iptables -I FORWARD','-i', nat.intfs[0], '-d', subnet, '-j DROP' )
        nat.cmd( 'iptables -A FORWARD','-i', nat.intfs[0], '-s', subnet, '-j ACCEPT' )
        nat.cmd( 'iptables -A FORWARD','-o', nat.intfs[0], '-d', subnet, '-j ACCEPT' )
        nat.cmd( 'iptables -t nat -A POSTROUTING','-s', subnet, "'!'", '-d', subnet,'-j MASQUERADE' )

    #info( "*** Testing network connectivity\n" )
    # net.pingAll()

    info( '*** Network is fully configured. Starting CLI\n')
    CLI(net)
    info( '*** Removing NAT rules\n')
    for subnet in ['192.168.1.0/24', '192.168.2.0/24']:
        nat.cmd( 'iptables -D FORWARD','-i', nat.intfs[0], '-d', subnet, '-j DROP' )
        nat.cmd( 'iptables -D FORWARD','-i', nat.intfs[0], '-s', subnet, '-j ACCEPT' )
        nat.cmd( 'iptables -D FORWARD','-o', nat.intfs[0], '-d', subnet, '-j ACCEPT' )
        nat.cmd( 'iptables -t nat -D POSTROUTING','-s', subnet, '\'!\'', '-d', subnet,'-j MASQUERADE' )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'debug' )
    myNetwork()
