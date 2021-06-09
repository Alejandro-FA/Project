# UPF-Network_Arquitecture
Final project of the Network Arquitecture subject developed at Universitat Pompeu Fabra.

## Objective
Develop a Mininet network topology capable of connecting with the physical LAN of the computer.

## Installation / use guide:

## Project state
* (OPTIONAL) Add a DNS Server / configure the virtual machine to use a specific DNS server (which the mininet net will use too).
This way, instead of doing `ping 8.8.8.8` we could also do `ping www.google.com`.
* After having changed the VM Network configuration from `NAT` to `Bridged Adapter`, the command `mininet> nat ifconfig` already
gives the same public address than the one of the Virtual Machine. Therefore, the `nat` public IP address is already
configured.
* The only remaining task is to configure the nat (using port forwarding probably) so that it is capable of routing incoming packets
to the appropiate mininet host.