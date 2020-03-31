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
