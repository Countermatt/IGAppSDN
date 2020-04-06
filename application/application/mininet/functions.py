from mininet.log import output, info, error, warn, debug
from Tkinter import *

def dumpNodes(nodes):
    root=Toplevel()
    root.title('Dump')
    text1=Text(root,height=100,width=200)
    text1.config(state="normal")
    for node in nodes:
        text1.insert(INSERT,str(node.name)+' ')
        for intf in node.intfList():
            text1.insert(INSERT,str(intf)+':')
            if intf.link:
                intfs = [ intf.link.intf1, intf.link.intf2 ]
                intfs.remove( intf )
                text1.insert(INSERT,intfs[0])
            else:
                text1.insert(INSERT,' ')
        text1.insert(INSERT,'\n')
    text1.config(state='disabled')
    text1.pack()

def dumpNet(net):
    nodes = net.controllers + net.switches + net.hosts
    dumpNodes(nodes )

def pinghosts(net,hosts=None,timeout=None ):
    # should we check if running?
    print('we are in pinghosts')
    root=Toplevel()
    text1=Text(root,height=100,width=200)
    text1.config(state="normal")
    packets = 0
    lost = 0
    ploss = None
    if not hosts:
        print('nothosts')
        hosts = net.hosts
        #output( '*** Ping: testing ping reachability\n' )
        text1.insert(INSERT,'*** Ping: testing ping reachability\n')
    for node in hosts:
        #output( '%s -> ' % node.name )
        text1.insert(INSERT,str(node.name) + ' ' + '-> ')
        for dest in hosts:
            if node != dest:
                opts = ''
                if timeout:
                    opts = '-W %s' % timeout
                if dest.intfs:
                    result = node.cmd('ping -c1 %s %s' % (opts, dest.IP()))
                    if 'connect: Network is unreachable' in result:
                        (sent,received) = (1,0)
                    else:
                        r = r'(\d+) packets transmitted, (\d+)( packets)? received'
                        m = re.search(r,result)
                        if m is None:
                            #error( '*** Error: could not parse ping output: %s\n' % pingOutput)
                            text1.insert(INSERT,'*** Error: could not parse ping output: ' + str(result) + '\n')
                            (sent,received)=(1,0)
                        else:
                            (sent,received) = (int(m.group(1)),int(m.group(2)))
                            #sent, received = self._parsePing(result)
                else:
                    sent, received = 0, 0
                packets += sent
                if received > sent:
                    #error( '*** Error: received too many packets' )
                    text1.insert(INSERT,'*** Error: received too many packets')
                    #error( '%s' % result )
                    text1.insert(INSERT,str(result))
                    node.cmdPrint('route')
                    exit(1)
                lost += sent - received
                #output( ( '%s ' % dest.name ) if received else 'X ' )
                if received :
                    text1.insert(INSERT,str(dest.name))
                else:
                    text1.insert(INSERT,str('X'))
        #output( '\n' )
        text1.insert(INSERT,str('\n'))
    if packets > 0:
        ploss = 100.0 * lost / packets
        received = packets - lost
        #output( "*** Results: %i%% dropped (%d/%d received)\n" %
                #( ploss, received, packets ))
        text1.insert(INSERT,"*** Results: "+str(ploss)+' '+'dropped ('+str(received)+'/'+str(packets)+'received)\n')
    else:
        ploss = 0
        #output( "*** Warning: No packets sent\n" )
        text1.insert(INSERT,"*** Warning: No packets sent\n")
    text1.config(state='disabled')
    text1.pack()
    return ploss
