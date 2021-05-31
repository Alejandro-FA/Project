#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.nodelib import NAT

def myNetwork():

    net = Mininet(topo=None, build=False, ipBase='10.0.0.0/8')

    info( '*** Add switches\n')
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch, failMode='standalone')
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, failMode='standalone')
    s0 = net.addSwitch('s0', cls=OVSKernelSwitch, failMode='standalone')

    info( '*** Add routers\n')
    # Since we specify the IP adresses for each interface later, we can simply put ip=None
    r1 = net.addHost('r1', cls=Node, ip='0.0.0.0')
    r3 = net.addHost('r3', cls=Node, ip='0.0.0.0')

    info( '*** Configuring NAT\n')
    # Add NAT connectivity
    nat0 = net.addHost('nat0', cls=NAT, ip='10.10.10.5/28', subnet='10.10.10.4/28', inetIntf='nat0-eth0', localIntf='nat0-eth1')
    
    info( '*** Add hosts\n')
    # Be very careful with the addresses used (defaultRoute must not include the mask '/24', but ip needs it)
    h1 = net.addHost('h1', cls=Host, ip='192.168.1.2/24', defaultRoute='via 192.168.1.1')
    h2 = net.addHost('h2', cls=Host, ip='192.168.1.3/24', defaultRoute='via 192.168.1.1') 
    h3 = net.addHost('h3', cls=Host, ip='192.168.1.4/24', defaultRoute='via 192.168.1.1')
    h4 = net.addHost('h4', cls=Host, ip='192.168.2.2/24', defaultRoute='via 192.168.2.1')
    h5 = net.addHost('h5', cls=Host, ip='192.168.2.3/24', defaultRoute='via 192.168.2.1')
    h6 = net.addHost('h6', cls=Host, ip='192.168.2.4/24', defaultRoute='via 192.168.2.1')
    
    info( '*** Add links\n')
    # With the addLink command we can create multiple interfaces for a router.
    # Furthermore, it is possible to specify an IP address for each of the interfaces of a router.
    net.addLink(r1, r3, intfName1='r1-eth1', params1={'ip':'10.10.10.1/30'},intfName2='r3-eth1', params2={'ip':'10.10.10.2/30'})
    net.addLink(s2, r1,intfName2='r1-eth0', params2={'ip':'192.168.1.1/24'})
    net.addLink(s4, r3,intfName2='r3-eth0', params2={'ip':'192.168.2.1/24'})

    net.addLink(s0, r3, intfName2='r3-eth2', params2={'ip':'10.10.10.6/28'})
    net.addLink(s0, r1, intfName2='r1-eth2', params2={'ip':'10.10.10.7/28'})
    net.addLink(s0, nat0, intfName2='nat0-eth1', params2={'ip':'10.10.10.5/28'})

    net.addLink(h1, s2)
    net.addLink(h2, s2)
    net.addLink(h3, s2)
    net.addLink(h4, s4)
    net.addLink(h5, s4)
    net.addLink(h6, s4)

    info( '*** Starting network\n')
    net.build()
    
    info( '*** Configuring routers interfaces\n')
    # Notice that commands have to be executed after net.build()
    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r3.cmd('sysctl -w net.ipv4.ip_forward=1')
    nat0.cmd('sysctl -w net.ipv4.ip_forward=1')
    # Command to configure the routers interfaces with the IP address and the netmask.
    r1.cmd('ifconfig r1-eth0 192.168.1.1 netmask 255.255.255.0 up')
    r1.cmd('ifconfig r1-eth1 10.10.10.1 netmask 255.255.255.252 up')
    r1.cmd('ifconfig r1-eth2 10.10.10.7 netmask 255.255.255.240 up')
    r3.cmd('ifconfig r3-eth0 192.168.2.1 netmask 255.255.255.0 up')
    r3.cmd('ifconfig r3-eth1 10.10.10.2 netmask 255.255.255.252 up')
    r3.cmd('ifconfig r1-eth2 10.10.10.6 netmask 255.255.255.240 up')

    info( '*** Configuring static routes\n')
    # Command to specify static routes
    r1.cmd('ip route add 192.168.2.0/24 via 10.10.10.2 dev r1-eth1')
    r3.cmd('ip route add 192.168.1.0/24 via 10.10.10.1 dev r3-eth1')

    info( '*** Starting switches\n')
    net.get('s4').start([])
    net.get('s2').start([])
    net.get('s0').start([])

    print( "Testing network connectivity" )
    net.pingAll()

    info( '*** Post configure switches and hosts\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

