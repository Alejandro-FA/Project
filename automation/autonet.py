#!/usr/bin/python
"""
Our network:
          nat0
           |
   r1 ----------- r3
    |              |
   s2             s4
    |              |
 h1 h2 h3       h4 h5 h6
"""

from mininet.net import Mininet
from mininet.node import Host, Node, OVSKernelSwitch
from mininet.nodelib import NAT
from mininet.cli import CLI
from mininet.log import setLogLevel, info, warn
from mininet.util import irange
from networks import Network

def NATNetwork(nnets=2, nhosts=3, netN_IP='172.16.0.0/16', netR_IP='10.10.10.0/24', netH_IP='192.168.0.0/16'):
    # Networks IP management
    netN = Network(netN_IP) # NAT-router network
    netR = Network(netR_IP) # router-router network
    netH = Network(netH_IP) # router-host network

    # Topology creation
    info( '*** Creating Network Topology\n')
    net = Mininet(topo=None)
    nat = net.addHost(name='nat', cls=NAT, connect=None, ip=None, inetIntf='nat-eth0')
    # nat0 = net.addNAT(name='nat0', connect=True, ip='0.0.0.0', inetIntf='nat0-eth0')
    for i in irange(1, nnets):
        # Add switch and router
        s = net.addSwitch(name='s%d' % i, cls=OVSKernelSwitch, failMode='standalone')
        r = net.addHost(name='r%d' % i, cls=Node, ip=None, mac=None) # ip=None prevents net.build() from messing up our intfs

        # Connect swtich with router (router-host subnet)
        subnetH = netH.addSubnet(minIntfs=254) # minIntfs=nhosts is more efficient
        rIntf = 'r%d-eth%d' % (i, i)
        net.addLink(r, s, intfName1=rIntf, port1=i, params1={'ip':subnetH.addIntf(rIntf)+'/'+subnetH.mask})

        # Add inet hosts and connect them with switch and router
        for j in irange(1, nhosts):
            h = net.addHost(name='h%d' % (j + nhosts*(i-1)), cls=Host, ip=None, mac=None) # ip=None prevents net.build() from messing up our intfs
            hIntf = 'h%d-eth1' % (j + nhosts*(i-1))
            net.addLink(s, h, intfName2=hIntf, port2=1, params2={'ip':subnetH.addIntf(hIntf)+'/'+subnetH.mask})
            h.setDefaultRoute('dev '+hIntf+' via '+subnetH.ip(rIntf))

        # Connect router with NAT (NAT-router network)
        # # TODO: This connection is not correctly done. How should we connect multiple routers to a NAT?
        #         IDEA: Using a switch or using a subnet for each nat-router pair
        natIntf = 'nat-eth%d' % i
        rIntf = 'r%d-eth%d' % (i, nnets+1)
        net.addLink(nat, r,
            intfName1=natIntf, params1={'ip':netN.addIntf(natIntf)+'/'+netN.mask},
            intfName2=rIntf, port2=nnets+1, params2={'ip':netN.addIntf(rIntf)+'/'+netN.mask}
            )
        r.setDefaultRoute('dev '+rIntf+' via '+netN.ip(natIntf))
        nat.cmd('ip route add '+subnetH.netIP+' dev '+natIntf+' via '+netN.ip(rIntf))

        # Connect router with previous routers in a mesh topology (router-router subnets)
        for j in irange(1, i-1):
            subnetR = netR.addSubnet(minIntfs=2)
            r1Intf = 'r%d-eth%d' % (i, j)
            r2Intf = 'r%d-eth%d' % (j, i)
            net.addLink(r, net.get('r%d' % j),
            intfName1=r1Intf, port1=j, params1={'ip':subnetR.addIntf(r1Intf)+'/'+subnetR.mask},
            intfName2=r2Intf, port2=i, params2={'ip':subnetR.addIntf(r2Intf)+'/'+subnetR.mask}
            )
            r.cmd('ip route add '+netH.subnets[j-1].netIP+' dev '+r1Intf+' via '+subnetR.ip(r2Intf))
            net.get('r%d'%j).cmd('ip route add '+netH.subnets[i-1].netIP+' dev '+r2Intf+' via '+subnetR.ip(r1Intf))

        # Start Network devices
        s.start([])

    # Build network
    info( '*** Starting network\n')
    net.build() # # NOTE: net.build() also calls nat.configDefault()!
    info( "*** Testing network connectivity" )
    # net.pingAll()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('debug')
    NATNetwork(nnets=3, nhosts=3)
