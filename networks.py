from mininet.util import netParse, ipParse, ipStr

class Network(object):
    def __init__(self, netIP='10.0.0.0/8'):
        """netIP: CIDR style network IP address"""
        self.netIP = netIP
        self.baseAdr, self.mask = netIP.split('/')
        self.nextAdr = ipStr(ipParse(self.baseAdr) + 1)
        self.maxIntfs = 2**(32 - int(self.mask)) - 2
        self.intfs = {}
        self.nIntfs = 0
        self.subnets = None

    def ip(self, intfName):
        # Convenient method getting IP address of an interface of the net
        return self.intfs[intfName]

    def addIntf(self, name):
        if self.nextAdr is None:
            if self.subnets is not None:
                warn("Adding interface", name, "to subnet", self.subnets[-1].netIP, "\n")
                return self.subnets[-1].addIntf(name)
            else:
                info("There aren't addresses available. Inteface", name, "has not been added to", self.netIP, "\n")
        else:
            self.intfs[name] = self.nextAdr
            self.nIntfs += 1
            if self.nIntfs == self.maxIntfs:
                self.nextAdr = None
            else:
                self.nextAdr = ipStr(ipParse(self.nextAdr) + 1)
            return self.ip(name)

    def addSubnet(self, minIntfs):
        # A network that has been divided into subnets cannot be used anymore
        if self.intfs:
            info('*** Deleting previous Network interfaces\n')
            self.intfs.clear()
        self.nextAdr = None
        self.hosts = None

        # Compute subnet IP
        hostbits = (minIntfs+1).bit_length() # Equivalent to ceil(log2(minIntfs+2))
        subnetMask = str(32 - hostbits)
        if self.subnets is None:
            self.subnets = []
            subnetIP = self.baseAdr
        elif (int(subnetMask) < int(self.subnets[-1].mask)):
            subnetIP = ipStr(2**hostbits + ipParse(self.subnets[-1].baseAdr))
        else:
            subnetIP = ipStr(self.subnets[-1].maxIntfs + 2 + ipParse(self.subnets[-1].baseAdr))

        # Create network and add it as a subnet
        subnet = Network(netIP=(subnetIP+'/'+subnetMask))
        self.subnets.append(subnet)
        return subnet
