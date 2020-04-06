from tkinter import *
from topo import Topo
from net import Mininet
from functions import dumpNodes,dumpNet,pinghosts
from cli import CLI
from log import setLogLevel

class SingleSwitchTopo(Topo):
    "Single switch connected to n hosts."
    def build(self, n=2):
        switch = self.addSwitch('s1')
        # Python's range(N) generates 0..N-1
        for h in range(n):
            host = self.addHost('h%s' % (h + 1))
            self.addLink(host, switch)

def simpleTest():
    "Create and test a simple network"
    topo = SingleSwitchTopo(n=4)
    net = Mininet(topo)
    net.start()
    # print("Dumping host connections")
    # dumpNet(net)
    h1, h4 = net.get( 'h1', 'h4' )
    net.do_pingpairfull()
    #net.iperf((h1, h4))

    # h1 = net.get('h1')
    # result = h1.cmd('ifconfig')

    #pinghosts(net,hosts=None,timeout=None)

    # print "Testing network connectivity"
    # net.pingAll()
    # #print result
    #
    # print ("Testing network connectivity")
    # net.pingAll()
    net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    simpleTest()
