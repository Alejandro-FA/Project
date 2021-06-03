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

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.util import irange
from mininet.nodelib import NAT

class InternetTopo(Topo):
	# max_hosts = 254
	# max_nets = 64

    def build(self, nnets=2, nhosts=3, **_kwargs ):
        routers = []
        for i in irange(1, nnets):
			# Add switch and router
			info( '*** Adding network %d switch and router\n' % i)
			s = self.addSwitch('s%d' % i, cls=OVSKernelSwitch, failMode='standalone')
			r = self.addHost('r%d' % i, cls=Node, ip='0.0.0.0', defaultRoute='via 172.16.%d.1' % i)
			self.addLink(r, s, intfName1='r%d-eth%d' % (i, i), params1={'ip':'192.168.%d.1/24' % i})
			routers.append(r)

			# Add inet hosts
			info( '*** Adding hosts for network %d\n' % i)
			for j in irange(1, nhosts):
				h = self.addHost('h%d' % (j + nhosts*(i-1)), cls=Host, ip='192.168.%d.%d/24' % (i, j+1), defaultRoute='via 192.168.%d.1' % i)
				self.addLink(h, s)

		# Adding NAT to topology
        info( '*** Adding and configuring NAT\n')
        # nat0 = self.addNAT('nat0', connect=True, ip='0.0.0.0', inetIntf='nat0-eth0')
        nat0 = self.addHost('nat0', cls=NAT, connect=True, ip='0.0.0.0', inetIntf='nat0-eth0')

        # Add links between each router and the NAT
        info( '*** Adding links between routers\n')
        for i in irange(1, nnets):
            self.addLink(nat0, routers[i-1], intfName1='nat0-eth%d' % i, params1={'ip':'172.16.%d.1/30' % i},
                        intfName2='r%d-eth0' % i, params2={'ip':'172.16.%d.2/30' % i})

        # Add links between the routers (mesh topology)
        subnet_count = 0
        for i in irange(1, nnets):
            for j in irange(i+1, nnets):
                self.addLink(routers[i-1], routers[j-1], intfName1='r%d-eth%d' % (i, j), params1={'ip':'10.10.10.%d/30' % (subnet_count*4 + 1)},
							intfName2='r%d-eth%d' % (j, i), params2={'ip':'10.10.10.%d/30' % (subnet_count*4 + 2)})

    def start():
        pass

def run():
    "Create network and run the CLI"
    topo = InternetTopo()
    net = Mininet(topo=topo, waitConnected=True)
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
