from mininet.util import ipParse, ipStr
from mininet.log import info
from collections import OrderedDict

class Network(object):
    def __init__(self, ip='10.0.0.0/8', nextSubnet=None):
        """ip: a.b.c.d/x network IP address
           nextSubnet: a.b.c.d next subnet IP address"""
        self.ip = ip
        self.baseAdr, self.mask = ip.split('/')
        self.nextAdr = ipStr(ipParse(self.baseAdr) + 1)
        self.maxHosts = 2**(32 - int(self.mask)) - 2
        self.hosts = OrderedDict()
        self.nHosts = 0
        self.subnets = []
        if nextSubnet is None:
            self.nextSubnet = self.baseAdr
        else:
            self.nextSubnet = nextSubnet

    def hostIP(self, name):
        # Get IP (a.b.c.d/x) address of a host by its name
        return self.hosts[name] + '/' + self.mask

    def giveIP(self, name):
        # Give ip (a.b.c.d) to a host of name 'name' and add it to the Network
        if self.nextAdr is None:
            if self.subnets is not None:
                info("Adding host", name, "to subnet", self.subnets[-1].ip,"\n")
                return self.subnets[-1].giveIP(name)
            else:
                info("There aren't addresses available. Host",
                       name, "has not been added to", self.ip,"\n")
        else:
            self.hosts[name] = self.nextAdr
            self.nHosts += 1
            if self.nHosts == self.maxHosts:
                self.nextAdr = None
            else:
                self.nextAdr = ipStr(ipParse(self.nextAdr) + 1)
            return self.hostIP(name) # Return IP (a.b.c.d/x) of the newly added host

    def addSubnet(self, minHosts):
        # A network that has been divided into subnets cannot be used anymore
        if self.hosts:
            info("Deleting previous hosts of the Network...\n")
            self.hosts.clear()
        self.nextAdr = None

        # Compute Subnet IP Address
        hostbits = (minHosts+1).bit_length() # Equivalent to ceil(log2(minHosts+2))
        subnetMask = 32 - hostbits
        if self.subnets and (subnetMask < int(self.subnets[-1].mask)):
            subnetAdr = ipStr(self.subnets[-1].maxHosts + 2 +
                              ipParse(self.subnets[-1].baseAdr))
        else:
            subnetAdr = self.nextSubnet

        # Create Subnet and return
        subnet = Network(subnetAdr + '/' + str(subnetMask))
        self.subnets.append(subnet)
        self.nextSubnet = ipStr(2**hostbits + ipParse(subnetAdr))
        return subnet

    def show(self):
        info("Network IP Address:", self.ip,"\n")
        for name, ip in self.hosts.items():
            info("  ", name + ":", ip,"\n")

        for s in self.subnets:
            info("  Subnet:", s.ip, "\n")
            for name, ip in s.hosts.items():
                info("    ", name + ":", ip,"\n")

        info("\n")
