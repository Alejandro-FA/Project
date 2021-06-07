#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Host, Node
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.nodelib import NAT

def myNetwork():

    net = Mininet(topo=None, build=False, ipBase='172.16.0.0/16')

    info( '*** Add switches\n')
    s0 = net.addSwitch('s0', cls=OVSKernelSwitch, failMode='standalone')
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, failMode='standalone')
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch, failMode='standalone')

    info( '*** Add routers\n')
    # Since we specify the IP adresses for each interface later, we can simply put ip=None
    r1 = net.addHost('r1', cls=Node, ip=None, defaultRoute='dev r1-eth2 via 172.16.0.1')
    r3 = net.addHost('r3', cls=Node, ip=None, defaultRoute='dev r3-eth2 via 172.16.0.1')

    info( '*** Configuring NAT\n')
    # Add NAT connectivity
    # nat0 = net.addNAT('nat0', connect=None, ip=None, inetIntf='nat0-eth0')
    nat0 = net.addHost(name='nat0', cls=NAT, connect=None, ip=None, subnet='176.16.0.0/16')

    info( '*** Add hosts\n')
    # Be very careful with the addresses used (defaultRoute must not include the mask '/24', but ip needs it)
    h1 = net.addHost('h1', cls=Host, ip='192.168.1.2/24', defaultRoute='via 192.168.1.1')
    h2 = net.addHost('h2', cls=Host, ip='192.168.1.3/24', defaultRoute='via 192.168.1.1')
    h3 = net.addHost('h3', cls=Host, ip='192.168.1.4/24', defaultRoute='via 192.168.1.1')
    h4 = net.addHost('h4', cls=Host, ip='192.168.2.2/24', defaultRoute='via 192.168.2.1')
    h5 = net.addHost('h5', cls=Host, ip='192.168.2.3/24', defaultRoute='via 192.168.2.1')
    h6 = net.addHost('h6', cls=Host, ip='192.168.2.4/24', defaultRoute='via 192.168.2.1')

    info( '*** Add links\n')
    # router-router subnet
    net.addLink(r1, r3, intfName1='r1-eth1', params1={'ip':'10.10.10.1/30'},intfName2='r3-eth1', params2={'ip':'10.10.10.2/30'})

    # nat-router subnet
    net.addLink(s0, nat0, intfName2='nat0-eth1', params2={'ip':'172.16.0.1/16'})
    net.addLink(s0, r1, intfName2='r1-eth2', params2={'ip':'172.16.0.2/16'})
    net.addLink(s0, r3, intfName2='r3-eth2', params2={'ip':'172.16.0.3/16'})

    # host-router subnet
    net.addLink(s2, r1,intfName2='r1-eth0', params2={'ip':'192.168.1.1/24'})
    net.addLink(s4, r3,intfName2='r3-eth0', params2={'ip':'192.168.2.1/24'})
    net.addLink(h1, s2)
    net.addLink(h2, s2)
    net.addLink(h3, s2)
    net.addLink(h4, s4)
    net.addLink(h5, s4)
    net.addLink(h6, s4)

    info( '*** Configuring static routes\n')
    r1.cmd('ip route add 192.168.2.0/24 via 10.10.10.2 dev r1-eth1')
    r3.cmd('ip route add 192.168.1.0/24 via 10.10.10.1 dev r3-eth1')
    # r3.cmd('ip route add 176.16.0.0/16 via 10.10.10.1 dev r3-eth1')

    nat0.cmd('ip route add 192.168.1.0/24 via 172.16.0.2 dev nat0-eth1')
    nat0.cmd('ip route add 192.168.2.0/24 via 172.16.0.3 dev nat0-eth1')
    # nat0.cmd('ip route add 10.10.10.0/30 via 172.16.0.2 dev nat0-eth1')

    info( '*** Starting network\n')
    # net.start()
    net.build()
    info( '*** Starting switches\n')
    s0.start([])
    s2.start([])
    s4.start([])

    print( "Testing network connectivity" )
    net.pingAll()

    info( '*** Post configure switches and hosts\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()
