from Tkinter import *
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from cli import CLI

class SingleSwitchTopo(Topo):
    "Single switch connected to n hosts."
    def build(self, n=2):
        switch = self.addSwitch('s1')
        # Python's range(N) generates 0..N-1
        for h in range(n):
            host = self.addHost('h%s' % (h + 1))
            self.addLink(host, switch)

def topTest():
    topo = SingleSwitchTopo(n=4)
    net = Mininet(topo)
    net.start()
    h1=net.get('h1')
    h2=net.get('h2')
    #h2int1=h2.intf('h2-eth0')
    print(h1.cmd('ping -c 20 %s' % h2.IP()))
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topTest()
