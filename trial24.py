#!/usr/bin/python
# -*- coding: utf-8 -*-

from Tkinter import *
from PIL import Image,ImageTk
#from Tkinter import ttk
import ttk
from tkFont import Font
import tkFileDialog
import logging
from net import Mininet, VERSION
import matplotlib.pyplot as plt
#from Tkinter import filedialog as tkFileDialog
from util import netParse,ipAdd
from link import Link
from time import sleep
from link import TCLink, Intf, Link
from log import info
from log import debug
from log import warn,setLogLevel
from net import Mininet, VERSION
from util import netParse, ipAdd, quietRun
from util import buildTopo
from util import custom, customClass
from util import waitListening
from term import makeTerm, cleanUpScreens
from node import Controller, RemoteController, NOX, OVSController
from node import CPULimitedHost, Host, Node
from node import OVSSwitch, UserSwitch
from link import TCLink, Intf, Link
from distutils.version import StrictVersion
from cli import CLI
from moduledeps import moduleDeps
from topo import SingleSwitchTopo, LinearTopo, SingleSwitchReversedTopo
from topolib import TreeTopo
from node import IVSSwitch
from functools import partial
from subprocess import call
logging.basicConfig(level=logging.INFO)
import os
import json

MININET_VERSION = re.sub(r'[^\d\.]', '', VERSION)

#Création de classe pour le controlleur
class InbandController( RemoteController ):
    def checkListening( self ):
        return

#Création de classe pour les switchs
#classe customOVS qui hérite de la classe OVSSwitch
class customOvs(OVSSwitch):
        #Constructeur de la classe customOvs
    def __init__(self,name,failMode='secure',datapath='kernel',**params ):
            #On appelle le constructeur de la classe parente
        OVSSwitch.__init__(self,name,failMode=failMode,datapath=datapath,**params)
        self.switchIP=None

    def getSwitchIP(self):
        return self.switchIP

    def setSwitchIP(self, ip):
        self.switchIP=ip

    def start(self,switches):
        #starting switches
        OVSSwitch.start(self,switches)
        #Setting switch IP address
        if self.switchIP is not None:
            self.cmd('ifconfig',self,self.switchIP )

class LegacySwitch(OVSSwitch):
    def __init__(self,name,**params):
        OVSSwitch.__init__(self,name,failMode='standalone',**params )
        self.switchIP = None

class CustomUserSwitch(UserSwitch):
    #CustomUserSwitch hérite de UserSwitch
    def __init__(self,name,dpopts='--no-slicing',**kwargs):
        UserSwitch.__init__(self,name,**kwargs )
        self.switchIP = None

    def getSwitchIP(self):
        return self.switchIP

    def setSwitchIP(self, ip):
        self.switchIP = ip

    def start(self,controllers):
        UserSwitch.start(self,controllers)
        if self.switchIP is not None:
            if not self.inNamespace:
                self.cmd('ifconfig',self,self.switchIP)
            else:
                self.cmd('ifconfig lo',self.switchIP)

class LegacyRouter(Node):

    def __init__( self, name, inNamespace=True, **params ):
        Node.__init__( self, name, inNamespace, **params )

    def config( self, **_params ):
        if self.intfs:
            self.setParam(_params,'setIP',ip='0.0.0.0')
            r = Node.config(self, **_params )
            self.cmd('sysctl -w net.ipv4.ip_forward=1')
            return r

class Interface():

    def __init__(self,window):
        self.click_widget=False
        self.link=None
        self.linkWidget=None
        self.hostNumber=0
        self.switchNumber=0
        self.controllerNumber=0
        self.activeButton=None
        self.currentSelection=None
        self.lastSelection=None
        self.linkSource=None
        self.linkTarget=None
        self.selectedNode=None
        self.selectedLink=None
        self.nb_widget_canevas=0
        self.preferences={"dpctl": "","ipBase": "10.0.0.0/8","netflow": {"nflowAddId":0,"nflowTarget":"","nflowTimeout": "600"},"openFlowVersions": {"ovsOf10":1,"ovsOf11":0,"ovsOf12":0,"ovsOf13":0},"sflow" : {"sflowHeader": "128","sflowPolling": "30","sflowSampling": "400","sflowTarget": ""},"startCLI":0,"switchType": "ovs","terminalType": "xterm"}
        self.list_buttons={}
        self.buttons_canevas={}
        self.links={}
        self.itemToName={}
        self.liens=[]
        self.name_switch=[]
        self.nameswitch={}
        self.name_host=[]
        self.names=[]
        self.namecontroller={}
        self.net=None
        self.switchOptions={}
        self.hostOptions={}
        self.legacySwitchOptions={}
        self.legacyRouterOptions={}
        self.controllerOptions={}
        self.coordonnees={"i0":0,"j0":0,"i1":0,"j1":0}
        self.create_menu_bar(window)
        self.widgetToItem={}
        self.itemToWidget={}
        self.source={}
        self.hosts=[]
        self.nameToItem={}
        self.name_host={}
        self.link_object={}
        self.canvas=self.create_canvas(window)
        self.elements=['Switch','Host','Link','LegacyRouter','LegacySwitch','Controller']
        self.nodePref = {'Switch':'s','Host':'h','LegacyRouter':'r','LegacySwitch':'s','Controller':'c'}
        self.images=self.netImages()
        self.create_buttons(window)

        self.s = ttk.Style()
        #self.s.configure('TFrame', background='yellow')

        self.s.configure('Frame1.TFrame',background='red')
        self.s.configure('Frame2.TFrame',background='blue')
        self.s.configure('Frame3.TFrame',background='snow')

        self.systemOnglet = ttk.Notebook(window,width=1500)
        self.systemOnglet.place(x='55',y='0')

        self.firstOnglet = ttk.Frame(self.systemOnglet,width=1500,height=1500,style='Frame1.TFrame')
        self.firstOnglet.place(x='0',y='0')
        self.systemOnglet.add(self.firstOnglet,text='Topologie')

        self.secondOnglet = ttk.Frame(self.systemOnglet,width=1500,height=1500,style='Frame2.TFrame')
        self.secondOnglet.place(x='30',y='0')
        self.systemOnglet.add(self.secondOnglet,text='Tests de performance')

        self.thirdOnglet = ttk.Frame(self.systemOnglet,width=1500,height=1500,style='Frame3.TFrame')
        self.thirdOnglet.place(x='60',y='0')
        self.systemOnglet.add(self.thirdOnglet,text='Contrôleurs SDN')


    def create_menu_bar(self,window):
        mainmenu = Menu(window)
        helv36 = Font(family='Helvetica', size=10, weight='bold')
        sousmenu1=Menu(mainmenu,bg='white',tearoff=0)
        sousmenu1.add_command(label="New",font=helv36,command=self.nvTopology)
        sousmenu1.add_command(label="Open",font=helv36,command=self.loadTopology)
        sousmenu1.add_command(label="Save",font=helv36,command=self.saveTopology)
        sousmenu1.add_command(label="Export level 2 script",font=helv36)
        sousmenu1.add_command(label="Quit",font=helv36)
        mainmenu.add_cascade(label="File",menu=sousmenu1,font=helv36)

        sousmenu2=Menu(mainmenu,bg='white',tearoff=0)
        sousmenu2.add_command(label="Cut",font=helv36)
        sousmenu2.add_command(label="Preferences",font=helv36,command=self.setPreferences)
        mainmenu.add_cascade(label='Edit',menu=sousmenu2,font=helv36)

        sousmenu3=Menu(mainmenu,bg='white',font=helv36,tearoff=0)
        sousmenu3.add_command(label="Run",font=helv36)
        sousmenu3.add_command(label="Stop",font=helv36)
        sousmenu3.add_command(label="Show OVS Summary",font=helv36,command=self.ovsShow)
        sousmenu3.add_command(label="Root Terminal",font=helv36,command=self.display_shell)
        mainmenu.add_cascade(label='Run',menu=sousmenu3,font=helv36)

        sousmenu4=Menu(mainmenu,bg='white',tearoff=0)
        sousmenu4.add_command(label="Net",font=helv36,command=self.dumpNet)
        sousmenu4.add_command(label="Ifconfig",font=helv36,command=self.chooseNode)
        sousmenu4.add_command(label="Ping all hosts",font=helv36,command=self.pinghosts)
        sousmenu4.add_command(label="Ping pair",font=helv36,command=self.pingpair)
        sousmenu4.add_command(label="Iperf",font=helv36,command=self.iperf_test)
        sousmenu4.add_command(label="List of Nodes",font=helv36,command=self.list_nodes)
        sousmenu4.add_command(label="Nodes and links informations",font=helv36,command=self.node_info)
        sousmenu4.add_command(label="Ping packet",font=helv36,command=self.pingpacket)
        sousmenu4.add_command(label='Preferences informations',font=helv36,command=self.preferencesinformations)
        sousmenu4.add_command(label='ip a',font=helv36,command=self.ipa)
        sousmenu4.add_command(label='links',font=helv36,command=self.linkinfo)
        sousmenu4.add_command(label='Choose server and client',font=helv36,command=self.chooseServerClient)
        mainmenu.add_cascade(label='Command',font=helv36,menu=sousmenu4)

        sousmenu5=Menu(mainmenu,bg='white',tearoff=0)
        sousmenu5.add_command(label="About NetView",font=helv36)
        mainmenu.add_cascade(label='Help',font=helv36,menu=sousmenu5)

        window.config(menu=mainmenu)

    def create_canvas(self,window):
        #canvas = Canvas(window,width='1000',height='1000',bg='pink')
        canvas = Canvas(window,width='1500',height='1500',bg='SlateGray1')
        canvas.place(x='55',y='0')
        canvas.bind('<ButtonPress-1>',self.canvasHandle)
        #canvas.bind('<B1-Motion>',self.dragCanevas)
        #canvas.bind('<ButtonRelease-1>',self.dropCanevas)
        return canvas

    def preferencesinformations(self):
        root = Toplevel()
        text2 = Text(root)
        scroll = Scrollbar(root, command=text2.yview)
        text2.configure(yscrollcommand=scroll.set)
        text2.config(state="normal")
        text2.tag_configure('big',justify='center',font=('Helvetica',16,'bold'),foreground='RoyalBlue1',underline=1)
        text2.tag_configure('color',font=('Helvetica',16,'bold'),spacing1=30)
        text2.insert(END,'\nPreferences\n','big')
        if('dpctl' in self.preferences and len(self.preferences['dpctl'])>0):
            text2.insert(END,"DPCTL: " + str(self.preferences['dpctl'])+'\n')
        if('ipBase' in self.preferences and len(self.preferences['ipBase'])>0):
            text2.insert(END,"ipBase: " + str(self.preferences['ipBase'])+'\n')
        if(self.preferences['netflow']['nflowAddId']==0):
            text2.insert(END,'nFlowAddID : ' + 'Not checked'+'\n')
        else:
            text2.insert(END,'nFlowAddID : ' + 'Checked'+'\n')
        if(len(self.preferences['netflow']['nflowTarget'])>0):
            text2.insert(END,'nFlowTarget : ' + self.preferences['netflow']['nflowTarget'] +'\n')
        if(len(self.preferences['netflow']['nflowTimeout'])>0):
            text2.insert(END,'nFlowTimeout : ' + self.preferences['netflow']['nflowTimeout'] +'\n')
        if(len(self.preferences['sflow']['sflowHeader'])>0):
            text2.insert(END,'sflowHeader: ' + self.preferences['sflow']['sflowHeader'] +'\n')
        if(len(self.preferences['sflow']['sflowPolling'])>0):
            text2.insert(END,'sflowPolling: ' + self.preferences['sflow']['sflowPolling'] +'\n')
        if(len(self.preferences['sflow']['sflowSampling'])>0):
            text2.insert(END,'sflowSampling: ' + self.preferences['sflow']['sflowSampling'] +'\n')
        if(len(self.preferences['sflow']['sflowTarget'])>0):
            text2.insert(END,'sflowTarget: ' + self.preferences['sflow']['sflowTarget'] +'\n')
        if(self.preferences['startCLI']==0):
            text2.insert(END,'startCLI: ' + 'Not Checked' +'\n')
        else:
            text2.insert(END,'startCLI: ' + 'Checked' +'\n')
        if(len(self.preferences['switchType'])>0):
            text2.insert(END,'switchType: ' + self.preferences['switchType'] +'\n')
        if(len(self.preferences['terminalType'])>0):
            text2.insert(END,'terminalType: ' + self.preferences['terminalType'] +'\n')
        for cle,valeur in self.preferences['openFlowVersions'].items():
            if (valeur == 1) :
                text2.insert(END,cle + ' : ' + 'Checked'+'\n')
            else:
                text2.insert(END,cle + ' : ' + 'Not checked' + '\n')
        text2.config(state='disabled')
        text2.pack(side=LEFT)
        scroll.pack(side=RIGHT,fill=Y)

    def list_nodes(self):
        root=Toplevel()
        text2 = Text(root, height=10, width=40)
        scroll = Scrollbar(root, command=text2.yview)
        text2.configure(yscrollcommand=scroll.set)
        text2.tag_configure('big',justify='center',font=('Helvetica',16,'bold'),foreground='RoyalBlue1',underline=1)
        text2.tag_configure('color',font=('Helvetica',16,'bold'),spacing1=30)
        text2.insert(END,'\nAvailable nodes\n','big')
        #text2.pack(side=LEFT)
        #scroll.pack(side=RIGHT, fill=Y)
        text2.config(state="normal")
        for i in range(0,len(self.names)):
            text2.insert(END,self.names[i]+ ' ','color')
        text2.config(state='disabled')
        text2.pack(side=LEFT)
        scroll.pack(side=RIGHT,fill=Y)

    def ifconfig_test(self):
        root=Toplevel()
        text2=Text(root,height=50,width=100)
        scroll = Scrollbar(root, command=text2.yview)
        text2.configure(yscrollcommand=scroll.set)
        text2.tag_configure('big',justify='center',font=('Helvetica',16,'bold'),foreground='RoyalBlue1',underline=1)
        #text2.tag_configure('color',font=('Helvetica',16,'bold'),spacing1=30)
        text2.tag_configure('police',font=('Helvetica',13,'bold'))
        text2.config(state="normal")

        text2.insert(END,"\n" + str(list_nodes[0]) + "'s interfaces\n"+'\n' + '\n','big')
        if(list_nodes[0] in namehosts):
            for host in self.name_host.keys():
                 if(host == list_nodes[0]):
                     result1=self.net.get(host)
                     result2=result1.cmd('ifconfig')
                     text2.insert(END,result2,'police')
                     text2.config(state='disabled')
                     text2.pack(side=LEFT)
                     scroll.pack(side=RIGHT,fill=Y)
                     return

        if(list_nodes[0] in namecontrol):
            #print("listenodes[0]"+str(list_nodes[0]))
            for controller in self.namecontroller.keys():
                if(list_nodes[0]== controller):
                    result1=self.net.get(controller)
                    result2=result1.cmd('ifconfig')
                    text2.insert(END,result2,'police')
                    text2.config(state='disabled')
                    text2.pack(side=LEFT)
                    scroll.pack(side=RIGHT,fill=Y)
                    return

        if(list_nodes[0] in nameswitches):
            for switch in self.nameswitch.keys():
                if(list_nodes[0]== switch):
                    result1=self.net.get(switch)
                    result2=result1.cmd('ifconfig')
                    text2.insert(END,result2,'police')
                    text2.config(state='disabled')
                    text2.pack(side=LEFT)
                    scroll.pack(side=RIGHT,fill=Y)
                    return

    def changeifconfig(self,*args):
        list_nodes[0]=var_ifconfig.get()

    def chooseNode(self):
        global list_nodes
        global namehosts
        global namecontrol
        global nameswitches
        global var_ifconfig
        var_ifconfig=StringVar()
        namehosts=[]
        namecontrol=[]
        nameswitches=[]

        for hostname in self.name_host.keys():
            namehosts.append(hostname)

        for switch in self.nameswitch.keys():
            nameswitches.append(switch)

        for controller in self.namecontroller.keys():
            namecontrol.append(controller)

        #list of nodes's names
        namenode=namehosts+nameswitches+namecontrol
        #print(namenode)

        var_ifconfig.set(namenode[0])
        var_ifconfig.trace("w",self.changeifconfig)
        list_nodes=[namenode[0]]
        #print('listnodes'+str(list_nodes))
        root=Toplevel()
        root.geometry('300x130')

        helv36 = Font(family='Helvetica', size=10, weight='bold')
        label=Label(root,text='Nodes interfaces',font=helv36)
        label.place(x=100,y=0)

        label1=Label(root,text='Choose node',font=helv36)
        label1.place(x=110,y=30)

        dropDownMenu=OptionMenu(root,var_ifconfig,*namenode)
        dropDownMenu.place(x=85,y=60)

        bouton = Button(root,text='OK',command=self.ifconfig_test)
        bouton.place(x=175,y=60)


    def changehostname2(self,*args):
        host_names['host0']=var_name2.get()
        hostnodes[0]=self.name_host[host_names['host0']]
        #print("host_nodes"+str(host_nodes)+'\n')

    def changehostname3(self,*args):
        host_names['host1']=var_name3.get()
        hostnodes[1]=self.name_host[host_names['host1']]
        #print("host_nodes 1 " + str(host_nodes) + '\n')

    def iperf_test(self):

         global host_names
         host_names={}
         global hostnodes
         hostnodes=[]
         global var_name2
         global var_name3
         name_hosts=()
         for host in self.name_host.keys():
              name_hosts=name_hosts+(str(host),)

         print(name_hosts)

         root=Toplevel()
         root.geometry("700x700")

         # host_names contient les noms du 1er host se trouvant dans name_hists
         host_names['host0']=name_hosts[0]
         host_names['host1']=name_hosts[0]

         hostnodes=[self.name_host[host_names['host0']],self.name_host[host_names['host1']]]

         var_name2=StringVar()
         var_name2.trace("w",self.changehostname2)

         var_name3=StringVar()
         var_name3.trace("w",self.changehostname3)

         var_name2.set(name_hosts[0])
         var_name3.set(name_hosts[0])

         dropDownMenu=OptionMenu(root,var_name2,*name_hosts)
         dropDownMenu.place(x=350,y=110)

         dropDownMenu1=OptionMenu(root,var_name3,*name_hosts)
         dropDownMenu1.place(x=500,y=110)

         bouton = Button(root,text='OK',command=partial(self.iperff,hostnodes))
         bouton.place(x=300,y=600)


    def iperff( self, hosts=None, l4Type='TCP', udpBw='10M' ):
        """Run iperf between two hosts.
           hosts: list of hosts; if None, uses opposite hosts
           l4Type: string, one of [ TCP, UDP ]
           returns: results two-element array of server and client speeds"""
        root=Toplevel()
        text1=Text(root,height=100,width=200)
        text1.config(state="normal")
        if not quietRun( 'which telnet' ):
            #error( 'Cannot find telnet in $PATH - required for iperf test' )
            text1.insert(INSERT, 'Cannot find telnet in $PATH - required for iperf test')
            text1.config(state='disabled')
            text1.pack()
            return
        if not hosts:
            hosts = [self.hosts[0],self.hosts[-1]]
        else:
            assert len(hosts) == 2
        client, server = hosts
        #output( '*** Iperf: testing ' + l4Type + ' bandwidth between ' )
        text1.insert(INSERT,'*** Iperf: testing ' + l4Type + ' bandwidth between ')
        #output( "%s and %s\n" % ( client.name, server.name ) )
        text1.insert(INSERT,str(client.name) + ' and '+ str(server.name)+'\n')
        server.cmd( 'killall -9 iperf' )
        iperfArgs = 'iperf '
        bwArgs = ''
        if l4Type == 'UDP':
            iperfArgs += '-u '
            bwArgs = '-b ' + udpBw + ' '
        elif l4Type != 'TCP':
            raise Exception( 'Unexpected l4 type: %s' % l4Type )
        server.sendCmd( iperfArgs + '-s', printPid=True )
        servout = ''
        while server.lastPid is None:
            servout += server.monitor()
        while 'Connected' not in client.cmd(
            'sh -c "echo A | telnet -e A %s 5001"' % server.IP()):
            #output('waiting for iperf to start up')
            text1.insert(INSERT,'waiting for iperf to start up')
            sleep(.5)
        cliout = client.cmd( iperfArgs + '-t 5 -c ' + server.IP() + ' ' +
                           bwArgs )
        #debug( 'Client output: %s\n' % cliout )
        text1.insert(INSERT,'Client output: ' + str(cliout) + '\n')
        server.sendInt()
        servout += server.waitOutput()
        #debug( 'Server output: %s\n' % servout )
        text1.insert(INSERT,'Server output: ' + str(servout) + '\n')
        r = r'([\d\.]+ \w+/sec)'
        m = re.findall(r,servout)
        if m:
            #return m[-1]
            iperfservout=m[-1]
        else:
            # was: raise Exception(...)
            #error( 'could not parse iperf output: ' + iperfOutput )
            text1.insert(INSERT,'could not parse iperf output: ' + servout )
            iperfservout = ''

        r = r'([\d\.]+ \w+/sec)'
        m1 = re.findall(r,cliout)
        if m1:
            #return m[-1]
            iperfcliout=m1[-1]
        else:
            # was: raise Exception(...)
            #error( 'could not parse iperf output: ' + iperfOutput )
            text1.insert(INSERT,'could not parse iperf output: ' + cliout )
            iperfcliout = ''
        #result = [ self._parseIperf( servout ), self._parseIperf( cliout ) ]
        result = [iperfservout,iperfservout]
        if l4Type == 'UDP':
            result.insert( 0, udpBw )
        #output( '*** Results: %s\n' % result )
        text1.insert(INSERT,'*** Results: ')
        text1.insert(INSERT,result)
        text1.insert(INSERT,'\n')
        text1.config(state='disabled')
        text1.pack()
        return result

    def ipeerf( self, hosts, l4Type, udpBw,seconds,port,timeServer,fichier):
        #hosts = hosts or [ self.hosts[ 0 ], self.hosts[ -1 ] ]
        print('l4Tyyyyyype'+l4Type[0])
        root1=Toplevel()
        text2=Text(root1,height=100,width=200)
        text2.config(state="normal")

        root=Toplevel()
        text1=Text(root,height=100,width=200)
        text1.config(state="normal")
        assert len( hosts ) == 2
        client, server = hosts
        # # output( '*** Iperf: testing', l4Type, 'bandwidth between',
        # #         client, 'and', server, '\n' )
        text1.insert(INSERT,'*** Iperf: testing '+str(l4Type[0])+' bandwidth between '+str(client.name)+ ' and '+str(server.name)+ '\n')
        server.cmd( 'killall -9 iperf' )
        # print(port)
        # print('\n')
        port1 = int(port.get())

        #serveur
        iperfArgs = 'iperf -p %d' % port1
        timeServer1 = int(timeServer.get())
        iperfArgs += ' -i %s '% timeServer1
        bwArgs = '-b ' + udpBw.get() + ' '
        if l4Type[0] == 'UDP':
             print('l4typeee : udppp')
             iperfArgs += '-u '
             bwArgs = '-b ' + udpBw.get() + ' '
        elif l4Type[0] != 'TCP':
        #     raise Exception( 'Unexpected l4 type: %s' % l4Type )
              text1.insert(INSERT,'Unexpected l4 type : ' + str(l4Type[0]))
              return
        # # if fmt:
        # #     iperfArgs += '-f %s ' % fmt
        server.sendCmd(iperfArgs + '-s')
        #client
        iperfArgs1='iperf -p %d ' % port1
        bwArgs1 = '-b ' + udpBw.get() + ' '
        if l4Type[0] == 'UDP':
             print('iperfArgs1:clieeent')
             iperfArgs1 += '-u '
             bwArgs1 = '-b ' + udpBw.get() + ' '
        elif l4Type[0] != 'TCP':
              text1.insert(INSERT,'Unexpected l4 type : ' + str(l4Type[0]))
              return

        if l4Type[0] == 'TCP':
            if not waitListening( client, server.IP(), port1):
                # raise Exception( 'Could not connect to iperf on port %d'
                #                  % port )
                text1.insert(INSERT,'Could not connect to iperf on port ' + port.get())
                return
        seconds1 = int(seconds.get())
        cliout = client.cmd( iperfArgs1 + '-t %d -c ' % seconds1 +
                             server.IP() + ' ' + bwArgs1)
        text1.insert(INSERT,'Client output: ' + cliout + '\n')
        text1.config(state='disabled')
        text1.pack(side=LEFT)
        servout = ''
        # We want the last *b/sec from the iperf server output
        # for TCP, there are two of them because of waitListening
        count = 2 if l4Type[0] == 'TCP' else 1
        while len( re.findall( '/sec', servout ) ) < count:
            servout += server.monitor( timeoutms=5000 )
        server.sendInt()
        servout += server.waitOutput()
        #debug( 'Server output: %s\n' % servout )
        text2.insert(INSERT,'Server output: ' + servout + '\n')
        text2.config(state='disabled')
        text2.pack(side=LEFT)
        file1 = open(fichier.get(),'w')
        file1.write(servout)
        file1.close()
        if(l4Type[0] == 'TCP'):
            file=open(fichier.get(),'r')
            lines = file.readlines()
            for line in lines:
                if 'sec' not in line:
                    lines.remove(line)

            for i in range(0,4):
                lines.remove(lines[0])

            for j in range(0,len(lines)):
                lines[j]=lines[j][6:38]

            lines.remove(lines[len(lines)-1])
            print(lines)
            print('\n')
            abscisse = []
            ordonnee = []

            for j in range(0,len(lines)):
                abscisse.append(float(lines[j][5:9]))
                ordonnee.append(float(lines[j][27:32]))

            print(abscisse)
            print('\n')
            print(ordonnee)

            plt.plot(abscisse,ordonnee)
            plt.axis([min(abscisse),max(abscisse)+1,0, max(ordonnee)+1])
            plt.xlabel('time')
            plt.ylabel('bandwidth')
            plt.show()

            file.close()
        elif(l4Type[0] == 'UDP'):
            file2=open(fichier.get(),'r')
            lines2 = file2.readlines()
            for line in lines2:
                if 'sec' not in line:
                    lines2.remove(line)

            #print(lines2)

            for i in range(0,3):
                 lines2.remove(lines2[0])

            lines2.remove(lines2[4])
            #print(lines2)
            #print('\n')

            lines2.remove(lines2[len(lines2)-1])

            # lines2.remove(lines2[len(lines2)-2])

            for j in range(0,len(lines2)):
                lines2[j]=lines2[j][6:38]

            print(lines2)

            lines2.remove(lines2[1])

            abscisse2=[]
            ordonnee2=[]
            for j in range(0,len(lines2)):
                abscisse2.append(float(lines2[j][5:9]))
                ordonnee2.append(float(lines2[j][27:32]))

            print(abscisse2)
            print(ordonnee2)

            plt.plot(abscisse2,ordonnee2)
            plt.axis([min(abscisse2),max(abscisse2)+1,0, max(ordonnee2)+1])
            plt.xlabel('time')
            plt.ylabel('bandwidth')
            plt.show()

            file2.close()
            # print(abscisse2)
            # print('\n')
            # print(ordonnee2)

        # result = [ self._parseIperf( servout ), self._parseIperf( cliout ) ]
        # if l4Type == 'UDP':
        #     result.insert( 0, udpBw )
        # output( '*** Results: %s\n' % result )
        # return result

    def pinghosts(self,hosts=None,timeout=None ):
        root=Toplevel()
        text1=Text(root,height=10,width=80)
        scroll = Scrollbar(root, command=text1.yview)
        text1.configure(yscrollcommand=scroll.set)
        text1.tag_configure('modif',justify='center',font=('Helvetica',12,'bold'),foreground='RoyalBlue1',underline=1)
        text1.tag_configure('police',justify='center',font=('Helvetica',12,'bold'))
        text1.tag_configure('police1',font=('Helvetica',12,'bold'))
        text1.config(state="normal")
        #hosts=self.hosts

        packets = 0
        lost = 0
        ploss = None
        if not hosts:
            #print('hosts are not null')
            hosts = self.hosts
            #print(hosts)
            #output( '*** Ping: testing ping reachability\n' )
            text1.insert(END,'\n\n*** Ping: testing ping reachability between hosts\n\n','modif')
        for node in hosts:
            #output( '%s -> ' % node.name )
            text1.insert(END,str(node.name) + ' ' + '-> ','police')
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
                                text1.insert(END,'*** Error: could not parse ping output: ' + str(result) + '\n','police')
                                (sent,received)=(1,0)
                            else:
                                (sent,received) = (int(m.group(1)),int(m.group(2)))
                                #sent, received = self._parsePing(result)
                    else:
                        sent, received = 0, 0
                    packets += sent
                    if received > sent:
                        #error( '*** Error: received too many packets' )
                        text1.insert(END,'*** Error: received too many packets','police')
                        #error( '%s' % result )
                        text1.insert(INSERT,str(result))
                        node.cmdPrint('route')
                        exit(1)
                    lost += sent - received
                    #output( ( '%s ' % dest.name ) if received else 'X ' )
                    if received :
                        text1.insert(INSERT,str(dest.name),'police1')
                    else:
                        text1.insert(INSERT,str('X'),'police1')
            #output( '\n' )
            text1.insert(INSERT,str('\n'))
        if packets > 0:
            ploss = 100.0 * lost / packets
            received = packets - lost
            #output( "*** Results: %i%% dropped (%d/%d received)\n" %
                    #( ploss, received, packets ))
            text1.insert(END,"*** Results: "+str(ploss)+' '+'dropped ('+str(received)+'/'+str(packets)+'received)\n','police')
        else:
            ploss = 0
            #output( "*** Warning: No packets sent\n" )
            text1.insert(END,"*** Warning: No packets sent\n",'police')
        text1.config(state='disabled')
        text1.pack(side=LEFT)
        scroll.pack(side=RIGHT,fill=Y)
        return ploss

    def changenode(self,*args):
        name1[0]=varnode.get()

    def ipa(self):
        global node1
        global name1

        listname=[]
        for switch in self.nameswitch.keys():
            listname.append(switch)
        for host in self.name_host.keys():
            listname.append(host)

        name1=[listname[0]]

        global varnode
        varnode=StringVar()
        varnode.set(listname[0])
        varnode.trace("w",self.changenode)

        root=Toplevel()
        text1=Text(root,height=10,width=80)
        scroll = Scrollbar(root, command=text1.yview)
        text1.configure(yscrollcommand=scroll.set)
        text1.tag_configure('modif',justify='center',font=('Helvetica',12,'bold'),foreground='RoyalBlue1',underline=1)
        text1.tag_configure('police',justify='center',font=('Helvetica',12,'bold'))
        text1.tag_configure('police1',font=('Helvetica',12,'bold'))
        text1.config(state="normal")
        dropdownmenu = OptionMenu(root,varnode,*listname)
        dropdownmenu.place(x=20,y=30)
        bouton=Button(root,text='OK',command=partial(self.ipa1,name1))
        bouton.place(x=80,y=30)
        text1.config(state='disabled')
        text1.pack(side=LEFT)
        scroll.pack(side=RIGHT,fill=Y)

    def ipa1(self,names):
        root=Toplevel()
        text1=Text(root)
        scroll = Scrollbar(root, command=text1.yview)
        text1.configure(yscrollcommand=scroll.set)
        text1.tag_configure('modif',justify='center',font=('Helvetica',12,'bold'),foreground='RoyalBlue1',underline=1)
        text1.tag_configure('police',justify='center',font=('Helvetica',12,'bold'))
        text1.tag_configure('police1',font=('Helvetica',12,'bold'))
        text1.config(state="normal")
        if names[0] in self.nameswitch.keys():
            node2=self.nameswitch[names[0]]
            links, _err, _result = node2.pexec( 'ip link show' )
            text1.insert(END,links)
            text1.config(state='disabled')
            text1.pack(side=LEFT)
            scroll.pack(side=RIGHT,fill=Y)
            return
        elif names[0] in self.name_host.keys():
            node2=self.name_host[names[0]]
            links, _err, _result = node2.pexec('ip link show')
            text1.insert(END,links)
            text1.config(state='disabled')
            text1.pack(side=LEFT)
            scroll.pack(side=RIGHT,fill=Y)

    def changename(self):
        name3[0]= varname1.get()

    def changename1(self):
        name4[0]=varname2.get()

    def linkinfo(self):
        listlinks=[]
        root=Toplevel()
        for link in self.links.keys():
            if(self.links[link]['type'] == 'data'):
                src=self.net.get(self.links[link]['src'])
                dst=self.net.get(self.links[link]['dest'])
                linkss=self.net.linksBetween(src,dst)
                listlinks.append(linkss)
        text1=Text(root)
        scroll = Scrollbar(root, command=text1.yview)
        text1.configure(yscrollcommand=scroll.set)
        text1.tag_configure('modif',justify='center',font=('Helvetica',12,'bold'),foreground='RoyalBlue1',underline=1)
        text1.tag_configure('police',justify='center',font=('Helvetica',12,'bold'))
        text1.tag_configure('police1',font=('Helvetica',12,'bold'))
        text1.config(state="normal")
        #print(linkss)
        for link2 in listlinks:
            text1.insert(INSERT,link2[0].__str__())
            text1.insert(INSERT,link2[0].status())
            text1.insert(INSERT,'\n')
        text1.config(state='disabled')
        text1.pack(side=LEFT)
        scroll.pack(side=RIGHT,fill=Y)


    def pingpacket1(self,hosts,number):
        root=Toplevel()
        text1=Text(root,height=10,width=80)
        scroll = Scrollbar(root, command=text1.yview)
        text1.configure(yscrollcommand=scroll.set)
        text1.tag_configure('modif',justify='center',font=('Helvetica',12,'bold'),foreground='RoyalBlue1',underline=1)
        text1.tag_configure('police',justify='center',font=('Helvetica',12,'bold'))
        text1.tag_configure('police1',font=('Helvetica',12,'bold'))
        text1.config(state="normal")
        h1=self.net.get(hosts['host0'])
        h2=self.net.get(hosts['host1'])
        #h2int1=h2.intf('h2-eth0')
        text1.insert(END,'\nExchanged packets between ' + hosts['host0'] + ' and '  + hosts['host1']+'\n'+'\n')
        result= h1.cmd('ping -c %s %s' % (number[0],h2.IP()))
        text1.insert(END,result)
        text1.config(state='disabled')
        text1.pack(side=LEFT)
        scroll.pack(side=RIGHT,fill=Y)

    #ping between two hosts
    def pinghosts1(self,hosts=None,timeout=None ):
        root=Toplevel()
        text1=Text(root,height=10,width=80)
        scroll = Scrollbar(root, command=text1.yview)
        text1.configure(yscrollcommand=scroll.set)
        text1.tag_configure('modif',justify='center',font=('Helvetica',12,'bold'),foreground='RoyalBlue1',underline=1)
        text1.tag_configure('police',justify='center',font=('Helvetica',12,'bold'))
        text1.tag_configure('police1',font=('Helvetica',12,'bold'))
        text1.config(state="normal")
        #hosts=self.hosts

        text1.insert(END,'\nPing : Testing ping reachability between ' + str(hosts[0]) + ' and ' + str(hosts[1]) + '\n\n','modif')
        packets = 0
        lost = 0
        ploss = None
        #if not hosts:
        #print('hosts are not null')
        #hosts = self.hosts
        #print(hosts)
        #output( '*** Ping: testing ping reachability\n' )
        #text1.insert(END,'\n\n*** Ping: testing ping reachability\n\n','modif')
        for node in hosts:
            #output( '%s -> ' % node.name )
            text1.insert(END,str(node.name) + ' ' + '-> ','police')
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
                                text1.insert(END,'*** Error: could not parse ping output: ' + str(result) + '\n','police')
                                (sent,received)=(1,0)
                            else:
                                (sent,received) = (int(m.group(1)),int(m.group(2)))
                                #sent, received = self._parsePing(result)
                    else:
                        sent, received = 0, 0
                    packets += sent
                    if received > sent:
                        #error( '*** Error: received too many packets' )
                        text1.insert(END,'*** Error: received too many packets','police')
                        #error( '%s' % result )
                        text1.insert(INSERT,str(result))
                        node.cmdPrint('route')
                        exit(1)
                    lost += sent - received
                    #output( ( '%s ' % dest.name ) if received else 'X ' )
                    if received :
                        text1.insert(INSERT,str(dest.name),'police1')
                    else:
                        text1.insert(INSERT,str('X'),'police1')
            #output( '\n' )
            text1.insert(INSERT,str('\n'))
        if packets > 0:
            ploss = 100.0 * lost / packets
            received = packets - lost
            #output( "*** Results: %i%% dropped (%d/%d received)\n" %
                    #( ploss, received, packets ))
            text1.insert(END,"*** Results: "+str(ploss)+' '+'dropped ('+str(received)+'/'+str(packets)+'received)\n','police')
        else:
            ploss = 0
            #output( "*** Warning: No packets sent\n" )
            text1.insert(END,"*** Warning: No packets sent\n",'police')
        text1.config(state='disabled')
        text1.pack(side=LEFT)
        scroll.pack(side=RIGHT,fill=Y)
        return ploss

    def create_buttons(self,window):
        abs=0;
        ord=0;
        helv36 = Font(family='Helvetica', size=10, weight='bold')
        for n in self.elements :
            cmd=(lambda t=n:self.activate_widget(t))
            self.list_buttons[n]=Button(window,height=50,width=50,bg='white') #switch , cursor , host
            self.list_buttons[n].config(relief="raised")
            self.list_buttons[n].config(image=self.images[n],command=cmd)
            self.list_buttons[n].place(x=str(abs),y=str(ord))
            ord+=60
        bouton1=Button(window,text='Run',command=self.run,bg='white',width=3,font=helv36)
        bouton1.place(x=str(abs),y=550)
        bouton2=Button(window,text='Stop',command=self.stop,bg='white',width=3,font=helv36)
        bouton2.place(x=str(abs),y=600)
        #print(self.list_buttons)

#activate a widget in the toolbar
    def activate_widget(self,nodeName):
        if self.activeButton == None:
            self.list_buttons[nodeName].config(relief='sunken')
            self.activeButton=nodeName
        else:
            self.list_buttons[self.activeButton].config(relief="raised")
            self.list_buttons[nodeName].config(relief="sunken")
            self.activeButton=nodeName
            #print(self.activeButton)

    def nvTopology(self):
        for bouton in self.buttons_canevas.values():
            item=self.widgetToItem[bouton]
            self.canvas.delete(item)
        for i in range(0,len(self.liens)):
            self.canvas.delete(self.liens[i])
        self.buttons_canevas={}
        self.links={}
        self.coordonnees={"i0":0,"j0":0,"i1":0,"j1":0}
        self.liens=[]
        self.itemToWidget={}
        self.widgetToItem={}
        self.switchNumber=0
        self.hostNumber=0
        self.switchOptions={}
        self.hostOptions={}
        self.nameToItem={}
        self.name_host={}
        self.controllerOptions={}
        self.legacySwitchOptions={}
        self.legacyRouterOptions={}
        self.itemToName={}
        self.names=[]
        self.preferences={"dpctl": "","ipBase": "10.0.0.0/8","netflow": {"nflowAddId": "0","nflowTarget": "","nflowTimeout": "600"},"openFlowVersions": {"ovsOf10": "1","ovsOf11": "0","ovsOf12": "0","ovsOf13": "0"},"sflow" : {"sflowHeader": "128","sflowPolling": "30","sflowSampling": "400","sflowTarget": ""},"startCLI": "0","switchType": "ovs","terminalType": "xterm"}
        self.openFlowVersions=[]

    def selectItem(self,item):
        self.lastSelection=self.selection
        self.currentSelection=item

    def addNodeToCanvas(self,nodeName,x,y):
        if (nodeName== 'Switch'):
            self.switchNumber += 1
        if (nodeName =='Host'):
            self.hostNumber += 1
        if (nodeName == 'Controller'):
            self.controllerNumber += 1
        icon=Button(self.canvas,image=self.images[nodeName])
        item=self.canvas.create_window(x,y,anchor='center',window=icon)
        self.widgetToItem[icon]=item
        self.itemToWidget[item]=icon

    def display_shell(self):
         root=Tk()
         root.geometry("700x400")
         termf = Frame(root,height=500,width=700)
         #termf.pack(fill=BOTH, expand=YES)
         termf.place(x=0,y=0)
         wid = termf.winfo_id()
         os.system('xterm -into %d -geometry 700x500 -sb &' % wid)
         root.mainloop()

    def xterm( self, _ignore=None ):
        "Make an xterm when a button is pressed."
        selectedNode=self.selectedNode
        itemNode=self.widgetToItem[selectedNode]
        name=self.itemToName[itemNode]
        if name not in self.net.nameToNode:
            return
        term = makeTerm(self.net.nameToNode[name],'Host',term=self.preferences['terminalType'])
        if (StrictVersion(MININET_VERSION)>StrictVersion('2.0')):
            self.net.terms += term
        else:
            self.net.terms.append(term)

    def make_draggable_host(self,widget):
         widget.bind("<Button-1>", self.click)
         widget.bind("<B1-Motion>", self.drag)
         widget.bind("<Button-3>",self.popup_host)
         widget.bind("<ButtonRelease-1>",self.release)

    def make_draggable_controller(self,widget):
         widget.bind("<Button-1>", self.click)
         widget.bind("<B1-Motion>", self.drag)
         widget.bind("<Button-3>",self.popup_controller)
         widget.bind("<ButtonRelease-1>",self.release)

    def make_draggable_switch(self,widget):
        widget.bind("<Button-1>", self.click)
        widget.bind("<B1-Motion>", self.drag)
        widget.bind("<Button-3>",self.popup_switch)
        widget.bind("<ButtonRelease-1>",self.release)

    def make_draggable_legacySwitch(self,widget):
        widget.bind("<Button-1>", self.click)
        widget.bind("<B1-Motion>", self.drag)
        widget.bind("<ButtonRelease-1>",self.release)
        widget.bind("<Button-3>",self.popup_legacyswitch)

    def make_draggable_legacyRouter(self,widget):
        widget.bind("<Button-1>", self.click)
        widget.bind("<B1-Motion>", self.drag)
        widget.bind("<ButtonRelease-1>",self.release)
        widget.bind("<Button-3>",self.popup_legacyrouter)

    def click(self,event):
        if (self.activeButton == "Link"):
            self.createLink(event)
        else:
            self.on_drag_start(event)

    def drag(self,event):
        if (self.activeButton == 'Link'):
            self.dragLink(event)
        else:
            self.on_drag_motion(event)

    def release(self,event):
        if (self.activeButton == "Link"):
            #print("helloo")
            self.finishLink(event)

    def on_drag_start(self,event):
        widget = event.widget
        widget._drag_start_x = event.x
        widget._drag_start_y = event.y

    def on_drag_motion(self,event):
        widget = event.widget
        item=self.widgetToItem[widget]
        x1,y1=self.canvas.coords(item)
        x = widget.winfo_x() - widget._drag_start_x + event.x
        y = widget.winfo_y() - widget._drag_start_y + event.y #coordonnées d'arrivée
        widget.place(x=x, y=y) #j'ai ajusté la position du noeud
        #on ajuste la position du lien
        # for valeur in self.links.keys():
        #     if(valeur == widget):
        #         for valeur1 in self.links[valeur].keys():
        #             link=self.links[valeur][valeur1]
        #             item1=self.widgetToItem[valeur1]
        #             x2,y2=self.canvas.coords(item1)
        #             self.canvas.coords(link,x,y,x2,y2)


    def popup_host(self,event):
        item=event.widget
        self.selectedNode=event.widget
        for bouton in self.list_buttons.values():
            etat_bouton =str(bouton['state'])
            if etat_bouton == 'disabled':
                popup_menu=Menu(self.canvas,tearoff=0)
                popup_menu.add_command(label="Terminal",command=self.xterm)
                popup_menu.post(event.x_root,event.y_root)
                return
        popup_menu=Menu(self.canvas,tearoff=0)
        popup_menu.add_command(label="Host Properties",command=self.hostProperties)
        popup_menu.post(event.x_root,event.y_root)

    def popup_controller(self,event):
        item=event.widget
        self.selectedNode=event.widget
        popup_menu=Menu(self.canvas,tearoff=0)
        popup_menu.add_command(label="Controller Properties",command=self.controllerProperties)
        popup_menu.post(event.x_root,event.y_root)

    def popup_switch(self,event):
        item=event.widget
        self.selectedNode=event.widget
        for bouton in self.list_buttons.values():
            etat_bouton =str(bouton['state'])
            if etat_bouton == 'disabled':
                popup_menu=Menu(self.canvas,tearoff=0)
                popup_menu.add_command(label="List Bridge",command=self.listBridge)
                popup_menu.post(event.x_root,event.y_root)
                return
        popup_menu=Menu(self.canvas,tearoff=0)
        popup_menu.add_command(label="Switch Properties",command=self.switchProperties)
        popup_menu.post(event.x_root,event.y_root)

    def popup_legacyswitch(self,event):
        item=event.widget
        self.selectedNode=event.widget
        for bouton in self.list_buttons.values():
            etat_bouton =str(bouton['state'])
            if etat_bouton == 'disabled':
                popup_menu=Menu(self.canvas,tearoff=0)
                popup_menu.add_command(label="List Bridge",command=self.listBridge)
                popup_menu.post(event.x_root,event.y_root)
                return

    def popup_legacyrouter(self,event):
        item=event.widget
        self.selectedNode=event.widget
        for bouton in self.list_buttons.values():
            etat_bouton =str(bouton['state'])
            if etat_bouton == 'disabled':
                popup_menu=Menu(self.canvas,tearoff=0)
                popup_menu.add_command(label="Terminal",command=self.xterm)
                popup_menu.post(event.x_root,event.y_root)
                return

    def popup_link(self,event):
        for bouton in self.list_buttons.values():
            etat_bouton =str(bouton['state'])
            #print("etat bouton" + etat_bouton)
            if etat_bouton == 'disabled':
                popup_menu=Menu(self.canvas,tearoff=0)
                popup_menu.add_command(label="Link down",command=self.linkDown)
                popup_menu.add_command(label="Link Up",command=self.linkUp)
                popup_menu.post(event.x_root,event.y_root)
                return
        popup_menu=Menu(self.canvas,tearoff=0)
        popup_menu.add_command(label="Link Properties",command=self.linkProperties)
        popup_menu.post(event.x_root,event.y_root)

    def chooseServerClient(self):
        global listentree
        listentree={}
        list_protocol=['TCP','UDP']
        global myprotocol
        global var_protocol

        var_protocol=StringVar()
        var_protocol.set(list_protocol[0])

        myprotocol=[list_protocol[0]]

        global hostserver
        hostserver=StringVar()

        global listenode

        global hostclient
        hostclient=StringVar()

        global liste
        name_hosts=()
        for host in self.name_host.keys():
            name_hosts=name_hosts+(str(host),)

        root=Toplevel()
        root.geometry('500x500')
        helv36 = Font(family='Helvetica', size=10, weight='bold')

        # listserver = [name_hosts[0]]
        # listclient = [name_hosts[0]]
        liste=[name_hosts[0],name_hosts[0]]
        listenode=[self.name_host[liste[0]],self.name_host[liste[0]]]
        hostserver.set(name_hosts[0])
        hostclient.set(name_hosts[0])
        hostserver.trace("w",self.changehostserver)
        hostclient.trace("w",self.changehostclient)

        label1=Label(root,text='Choose nodes',font=helv36)
        label1.place(x=10,y=10)

        label3=Label(root,text='server',font=helv36)
        label3.place(x=10,y=35)

        dropDownMenu=OptionMenu(root,hostserver,*name_hosts)
        dropDownMenu.place(x=90,y=35)

        label5=Label(root,text="Time")
        label5.place(x=10,y=65)
        entry_100=Entry(root,width=10)
        entry_100.place(x=75,y=65)
        listentree['timeserver']=entry_100

        label6 = Label(root,text="Port")
        label6.place(x=10,y=95)
        entry_101=Entry(root,width=10)
        entry_101.place(x=75,y=95)
        listentree['portserver']=entry_101

        label7 = Label(root,text="Protocol")
        label7.place(x=10,y=125)
        var_protocol.trace("w",self.changeprotocolserver)
        dropDownMenu3=OptionMenu(root,var_protocol,*list_protocol)
        dropDownMenu3.place(x=75,y=125)

        label95 = Label(root,text="fichier")
        label95.place(x=10,y=155)
        entry95=Entry(root,width=10)
        entry95.place(x=75,y=155)
        listentree['fichier']=entry95

        label100=Label(root,text='client',font=helv36)
        label100.place(x=250,y=35)
        dropDownMenu2=OptionMenu(root,hostclient,*name_hosts)
        dropDownMenu2.place(x=330,y=35)

        # label102=Label(root,text='Port')
        # label102.place(x=250,y=65)
        # entry102=Entry(root,width=10)
        # entry102.place(x=320,y=65)
        # listentree['portclient']=entry102

        # label103=Label(root,text='Protocol')
        # label103.place(x=250,y=65)
        # var_protocol1.trace("w",self.changeprotocolclient)
        # dropDownMenu4=OptionMenu(root,var_protocol1,*list_protocol)
        # dropDownMenu4.place(x=330,y=95)

        label105 = Label(root,text='Bandwidth')
        label105.place(x=250,y=95)
        entry105=Entry(root,width=10)
        entry105.place(x=330,y=95)
        listentree['bandwidth']=entry105

        label106 = Label(root,text='Transmission duration')
        label106.place(x=200,y=125)
        entry106=Entry(root,width=10)
        entry106.place(x=380,y=125)
        listentree['duration']=entry106

        # label107 = Label(root,text='ServerIp')
        # label107.place(x=250,y=155)
        # entry107=Entry(root,width=10)
        # entry107.place(x=350,y=155)
        # listentree['serverip']=entry107

        bouton1 = Button(root,text='OK',command=partial(self.ipeerf,listenode,myprotocol,listentree['bandwidth'],listentree['duration'],listentree['portserver'],listentree['timeserver'],listentree['fichier']))
        bouton1.place(x=200,y=225)

    # def setserver(self,server):
        # if(myprotocol[0] == 'tcp'):
        #     noeud=self.name_host[server[0]]
        #     resultat = noeud.cmd('iperf -s -p %s -i %s' % (listentree['portserver'].get(),listentree['timeServer'].get()))

    # def setclient(self,client):
    #     if(myprotocol[0] == 'tcp'):
    #         noeud=self.name_host[client[0]]
    #         resultat = noeud.cmd('iperf -c %s -b %s -t %s -p %s' % (listentree['serverip'].get(),listentree['bandwidth'].get(),listentree['duration'].get(),listentree['portclient'].get()))
    #         text1=Text(root,height=200,width=200)
    #         text1.config(state="normal")
    #         text1.insert(INSERT,resultat)
    #         text1.config(state='disabled')
    #         text1.pack()

    def changeprotocolserver(self,*args):
        myprotocol[0]=var_protocol.get()
        print('myprotocol')
        print(myprotocol)

    # def changeprotocolclient(self,*args):
    #     myprotocol1=[var_protocol1.get()]
    #     print('myprotocol1')
    #     print(myprotocol1)

    def changehostserver(self,*args):
        liste[1]=hostserver.get()
        listenode[1]=self.name_host[hostserver.get()]
        print('listenode')
        print(listenode)
        print('\n')

    def changehostclient(self,*args):
        liste[0]=hostclient.get()
        listenode[0]=self.name_host[hostclient.get()]
        print('listenode')
        print(liste)

    def listBridge( self, _ignore=None ):
        selectedNode=self.selectedNode  #widget
        itemNode=self.widgetToItem[selectedNode]
        name=self.itemToName[itemNode]
        tags = self.canvas.gettags(itemNode)

        if name not in self.net.nameToNode:
            return
        if 'Switch' in tags or 'LegacySwitch' in tags:
            call(["xterm -T 'Bridge Details' -sb -sl 2000 -e 'ovs-vsctl list bridge " + name + "; read -p \"Press Enter to close\"' &"], shell=True)

    @staticmethod
    def ovsShow(_ignore=None):
        call(["xterm -T 'OVS Summary' -sb -sl 2000 -e 'ovs-vsctl show; read -p \"Press Enter to close\"' &"],shell=True)

    def changeCPU(self,*args):
        hostEntries['sched']=varCPU.get()

    def addVLANInterface(self):
        listbox3.insert(END,content_vlan.get())
        listbox4.insert(END,content_vlan1.get())
        vlanEntries.append((content_vlan.get(),content_vlan1.get()))

    def addExternalInterface(self):
        listbox5.insert(END,content_external.get())
        externalEntries.append(content_external.get())

    def addDirectory(self):
        listbox10.insert(END,content_directory.get())
        listbox11.insert(END,content_directory1.get())
        directoryEntries.append((content_directory.get(),content_directory1.get()))

    def hostProperties(self):
        Options=['host','cfs','rt']
        global hostEntries
        hostEntries={}
        hostEntries['sched']=""
        global namehost
        namehost=StringVar()
        global varCPU
        varCPU=StringVar()
        global content_vlan
        content_vlan=StringVar()
        global content_vlan1
        content_vlan1=StringVar()
        global serv
        serv = IntVar()
        global listbox3
        global listbox4
        global listbox5
        global content_external
        global content_directory
        global content_directory1
        content_directory=StringVar()
        content_directory1=StringVar()
        global listbox10
        global listbox11
        content_external=StringVar()
        global vlanEntries
        vlanEntries=[]
        global externalEntries
        externalEntries=[]
        global directoryEntries
        directoryEntries=[]
        global clien
        clien=IntVar()
        fen = Toplevel()
        fen.geometry('500x500')
        nb = ttk.Notebook(fen)
        frame1=ttk.Frame(nb)
        frame2=ttk.Frame(nb)
        frame5=ttk.Frame(nb)
        frame6=ttk.Frame(nb)
        nb.add(frame1,text="Properties")
        nb.add(frame2,text="VLAN Interfaces")
        nb.add(frame5,text="External Interfaces")
        nb.add(frame6,text="Private Directories")
        nb.pack(fill="both",expand="yes")

        #hostname
        label_1=Label(frame1,text="Hostname :",width=20,font=("bold",10))
        label_1.place(x=1,y=20)

        namehost.set(self.hostOptions[self.selectedNode]['hostname'])
        entry_1=Entry(frame1,textvariable=namehost)
        entry_1.place(x=150,y=20)
        hostEntries['hostname']=entry_1

        #ipAddress
        label_2=Label(frame1,text="IP Address :",width=20,font=("bold",10))
        label_2.place(x=1,y=50)
        entry_2=Entry(frame1)
        entry_2.place(x=150,y=50)
        hostEntries['ipAddress']=entry_2

        #DefaultRoute
        label_3=Label(frame1,text="Default Route :",width=20,font=("bold",10))
        label_3.place(x=1,y=80)
        entry_3=Entry(frame1)
        entry_3.place(x=150,y=80)
        hostEntries['defaultRoute']=entry_3

        #CPU
        label_4=Label(frame1,text="Amount CPU :",width=20,font=("bold",10))
        label_4.place(x=1,y=110)
        varCPU.set(Options[0])
        varCPU.trace("w",self.changeCPU)
        dropDownMenu=OptionMenu(frame1,varCPU,Options[0],Options[1],Options[2])
        dropDownMenu.place(x=350,y=110)
        entry_4=Entry(frame1)
        entry_4.place(x=150,y=110)
        hostEntries['cpu']=entry_4

        #Cores
        label_5=Label(frame1,text="Cores :",width=20,font=("bold",10))
        label_5.place(x=1,y=140)
        entry_5=Entry(frame1)
        entry_5.place(x=150,y=140)
        hostEntries['cores']=entry_5

        #Start Command
        label_6=Label(frame1,text="Start Command :",width=20,font=("bold",10))
        label_6.place(x=1,y=170)
        entry_6=Entry(frame1)
        entry_6.place(x=150,y=170)
        hostEntries['start']=entry_6

        #Stop Command
        label_7=Label(frame1,text="Stop Command :",width=20,font=("bold",10))
        label_7.place(x=1,y=200)
        entry_7=Entry(frame1)
        entry_7.place(x=150,y=200)
        hostEntries['stop']=entry_7

        bouton1=Button(frame1,text="OK",width=8,height=2,command=self.logInformationsHost)
        bouton1.place(x=1,y=400)

        bouton2=Button(frame1,text="Cancel",width=8,height=2,command=lambda : fen.destroy())
        bouton2.place(x=100,y=400)

        #serveur ou pas serveur
        # label_100 = Label(frame1,text='Serveur iperf',width=20,font=('bold',10))
        # label_100.place(x=5,y=320)
        # bouton_serveur=Checkbutton(frame1,variable=serv,offvalue=0,onvalue=1)
        # bouton_serveur.select()
        # bouton_serveur.bind('<Button-1>',self.changeStatusServeur)
        # bouton_serveur.place(x=140,y=320)

        #client ou pas client
        # label_101=Label(frame1,text='Client Iperf',width=20,font=('bold',10))
        # label_101.place(x=200,y=320)
        # bouton_client =Checkbutton(frame1,variable=clien,offvalue=0,onvalue=1)
        # bouton_client.select()
        # bouton_client.bind('<Button-1>',self.changeStatusClient)
        # bouton_client.place(x=340,y=320)
        #
        # print('clien'+str(clien.get()))
        # print('serv'+str(serv.get()))

        #Frame 2 VLAN INTERFACE
        label_8=Label(frame2,text="VLAN Interface:",width=20,font=("bold",10))
        label_8.place(x=50,y=10)
        bouton3=Button(frame2,text='Add',command= self.addVLANInterface,width=5,height=1)
        bouton3.place(x=200,y=10)

        frame=Frame(frame2,highlightbackground="black", highlightcolor="black",highlightthickness=1,width=400,height=300,bd=0)
        frame.place(x=50,y=50)
        frame3 = Frame(frame, highlightbackground="black", highlightcolor="black", highlightthickness=1, width=200, height=20, bd= 0)
        frame3.place(x=20,y=10)

        label_9=Label(frame3,text="IP Address",width=20)
        label_9.pack()
        entry_9=Entry(frame3,textvariable=content_vlan)
        entry_9.pack()

        frame4 = Frame(frame, highlightbackground="black", highlightcolor="black", highlightthickness=1, width=200, height=20, bd= 0)
        frame4.place(x=180,y=10)
        label_10=Label(frame4,text="VLAN ID",width=20)
        label_10.pack()
        entry_10=Entry(frame4,textvariable=content_vlan1)
        entry_10.pack()

        scroll= Scrollbar(frame3)
        scroll.pack(side=RIGHT,fill=Y)
        listbox3=Listbox(frame3,yscrollcommand=scroll.set)
        listbox3.pack()
        scroll.config(command=listbox3.yview)

        scroll= Scrollbar(frame4)
        scroll.pack(side=RIGHT,fill=Y)
        listbox4=Listbox(frame4,yscrollcommand=scroll.set)
        listbox4.pack()
        scroll.config(command=listbox4.yview)

        #Frame5  External Interfaces

        label12=Label(frame5,text="External Interface :")
        label12.place(x=1,y=10)
        bouton12=Button(frame5,text='Add',command=self.addExternalInterface)
        bouton12.place(x=130,y=5)
        frame12=Frame(frame5,highlightbackground="black", highlightcolor="black",highlightthickness=1,width=250,height=300,bd=0)
        frame12.place(x=1,y=50)
        frame13=Frame(frame12,highlightbackground="black", highlightcolor="black",highlightthickness=1,width=200,height=20,bd=0)
        frame13.place(x=1,y=10)
        label13=Label(frame13,text="Interface Name")
        label13.pack()
        entry13=Entry(frame13,textvariable=content_external)
        entry13.pack()
        frame14=Frame(frame12,highlightbackground="black", highlightcolor="black",highlightthickness=1,width=200,height=300,bd=0)
        frame14.place(x=1,y=80)

        scroll= Scrollbar(frame14)
        scroll.pack(side=RIGHT,fill=Y)
        listbox5=Listbox(frame14,yscrollcommand=scroll.set)
        listbox5.pack()
        scroll.config(command=listbox5.yview)

        bouton11=Button(frame2,text="OK",width=10,height=2)
        bouton11.place(x=150,y=380)
        bouton12=Button(frame2,text="Cancel",command=lambda:fen.destroy(),width=10,height=2)
        bouton12.place(x=260,y=380)

        bouton13=Button(frame5,text="OK",width=10,height=2)
        bouton13.place(x=10,y=380)
        bouton14=Button(frame5,text="Cancel",command=lambda:fen.destroy(),width=10,height=2)
        bouton14.place(x=120,y=380)

        bouton15=Button(frame6,text="OK",width=10,height=2)
        bouton15.place(x=150,y=380)
        bouton16=Button(frame6,text="Cancel",command=lambda:fen.destroy(),width=10,height=2)
        bouton16.place(x=260,y=380)

        #frame 6 PRIVATE DIRECTORIES
        label_16=Label(frame6,text="Private Directory:",width=20,font=("bold",10))
        label_16.place(x=50,y=10)
        bouton11=Button(frame6,text='Add',command= self.addDirectory,width=5,height=1)
        bouton11.place(x=200,y=10)

        frame7=Frame(frame6,highlightbackground="black", highlightcolor="black",highlightthickness=1,width=400,height=300,bd=0)
        frame7.place(x=50,y=50)
        frame8 = Frame(frame7, highlightbackground="black", highlightcolor="black", highlightthickness=1, width=200, height=20, bd= 0)
        frame8.place(x=20,y=10)

        label_17=Label(frame8,text="Mount",width=20)
        label_17.pack()
        entry_20=Entry(frame8,textvariable=content_directory)
        entry_20.pack()

        frame9 = Frame(frame7, highlightbackground="black", highlightcolor="black", highlightthickness=1, width=200, height=20, bd= 0)
        frame9.place(x=180,y=10)
        label_10=Label(frame9,text="Persistent Directory",width=20)
        label_10.pack()
        entry_21=Entry(frame9,textvariable=content_directory1)
        entry_21.pack()

        scroll= Scrollbar(frame8)
        scroll.pack(side=RIGHT,fill=Y)
        listbox10=Listbox(frame8,yscrollcommand=scroll.set)
        listbox10.pack()
        scroll.config(command=listbox10.yview)

        scroll= Scrollbar(frame9)
        scroll.pack(side=RIGHT,fill=Y)
        listbox11=Listbox(frame9,yscrollcommand=scroll.set)
        listbox11.pack()
        scroll.config(command=listbox11.yview)

    # def changeStatusServeur(self,*args):
    #     print('valeur serveur'+str(serv.get()))
    #     print('\n')
    #
    #
    # def changeStatusClient(self,*args):
    #     print('valeur client'+str(clien.get()))
    #     print('\n')

    def logInformationsHost(self):
        setLogLevel( 'info' )
        newhostoptions={}
        newhostoptions['nodeNum']=self.hostOptions[self.selectedNode]['numhost']
        newhostoptions['hostname']=hostEntries['hostname'].get()
        newhostoptions['ip']=hostEntries['ipAddress'].get()
        newhostoptions['defaultRoute']=hostEntries['defaultRoute'].get()
        newhostoptions['cores']=hostEntries['cores'].get()
        newhostoptions['startCommand']=hostEntries['start'].get()
        newhostoptions['stopCommand']=hostEntries['stop'].get()
        newhostoptions['sched']=hostEntries['sched']
        newhostoptions['cpu']=hostEntries['cpu'].get()
        newhostoptions['externalInterfaces']=externalEntries
        newhostoptions['privateDirectory']=directoryEntries
        newhostoptions['vlanInterfaces']=vlanEntries
        newhostoptions['serveur']=serv.get()
        newhostoptions['client']=clien.get()
        self.hostOptions[self.selectedNode]['options']=newhostoptions
        info('New host details for ' + newhostoptions['hostname'] + '=' + str(newhostoptions) + '\n')

    def logInformationsController(self):
        setLogLevel('info')
        newcontrolleroptions={}
        newcontrolleroptions['hostname']=self.controllerOptions[self.selectedNode]['hostname']
        newcontrolleroptions['remotePort']=listProperties['remotePort'].get()
        newcontrolleroptions['remoteIP']=listProperties['remoteIP'].get()
        newcontrolleroptions['controllerType']=listProperties['controllerType']
        newcontrolleroptions['controllerProtocol']=listProperties['controllerProtocol']
        self.controllerOptions[self.selectedNode]['options']=newcontrolleroptions
        info('New controller details for' + newcontrolleroptions['hostname'] + '=' + str(newcontrolleroptions) + '\n')

    def changeControllerType(self,*args):
        listProperties['controllerType']=var25.get()

    def changeProtocol(self,*args):
        listProperties['controllerProtocol']=var26.get()

    def controllerProperties(self):
        root=Toplevel()
        root.geometry('300x320')
        global listProperties
        listProperties={}
        global var26
        var26=StringVar()
        global var25
        var25=StringVar()
        global name_controller
        name_controller=StringVar()
        global controller_port
        controller_port=StringVar()
        global controller_address
        controller_address=StringVar()
        Options=['OpenFlow Reference','Remote Controller','In-Band Controller','OVS Controller']
        optionsProtocol=['tcp','ssl']
        listProperties['controllerProtocol']=optionsProtocol[0]
        listProperties['controllerType']=Options[0]

        label1=Label(root,text='Name:')
        label1.place(x=1,y=10)
        name_controller.set(self.controllerOptions[self.selectedNode]['hostname'])
        entry20=Entry(root,textvariable=name_controller)
        entry20.place(x=120,y=10)
        listProperties['hostname']=entry20

        label2=Label(root,text='Controller Port:')
        label2.place(x=1,y=40)
        controller_port.set("6633")
        entry21=Entry(root,textvariable=controller_port)
        entry21.place(x=120,y=40)
        listProperties['remotePort']=entry21

        label3=Label(root,text='Controller Type:')
        label3.place(x=1,y=70)
        var25.set(Options[0])
        var25.trace("w",self.changeControllerType)
        dropDownMenu=OptionMenu(root,var25,Options[0],Options[1],Options[2],Options[3])
        dropDownMenu.place(x=120,y=70)

        label4=Label(root,text='Protocol:')
        label4.place(x=1,y=100)
        var26.set(optionsProtocol[0])
        var26.trace("w",self.changeProtocol)
        dropDownMenu1=OptionMenu(root,var26,optionsProtocol[0],optionsProtocol[1])
        dropDownMenu1.place(x=120,y=110)

        frame5=LabelFrame(root,text="Remote/In-Band Controller",width=280,height=60)
        frame5.place(x=10,y=150)
        label5=Label(frame5,text="IP Address:")
        label5.place(x=1,y=10)
        controller_address.set("127.0.0.1")
        entry22=Entry(frame5,textvariable=controller_address)
        entry22.place(x=90,y=10)
        listProperties['remoteIP']=entry22

        bouton1=Button(root,text='OK',width=5,height=1,command=self.logInformationsController)
        bouton1.place(x=50,y=230)
        bouton2=Button(root,text='Cancel',width=5,height=1,command=lambda:root.destroy())
        bouton2.place(x=150,y=230)

    def linkProperties(self):
        global linkEntries
        linkEntries={}
        root = Toplevel()
        root.geometry("350x250")

        #Bandwidth
        label_1=Label(root,text='Bandwidth:',width=15,font=("bold",10))
        label_1.place(x=0,y=10)
        entry_1=Entry(root)
        entry_1.place(x=125,y=10)
        linkEntries['bw']=entry_1
        label_7=Label(root,text='Mbit')
        label_7.place(x=290,y=10)

        #Delay
        label_2=Label(root,text='Delay:',width=15,font=("bold",10))
        label_2.place(x=0,y=40)
        entry_2=Entry(root)
        entry_2.place(x=125,y=40)
        linkEntries['delay']=entry_2

        #Loss
        label_3=Label(root,text='Loss:',width=15,font=("bold",10))
        label_3.place(x=0,y=70)
        entry_3=Entry(root)
        entry_3.place(x=125,y=70)
        label_8=Label(root,text='%')
        label_8.place(x=290,y=70)
        linkEntries['loss']=entry_3

        #Max Queue Size
        label_4=Label(root,text='Max Queue size:',width=15,font=("bold",10))
        label_4.place(x=0,y=100)
        entry_4=Entry(root)
        entry_4.place(x=125,y=100)
        linkEntries['max_queue_size']=entry_4

        #Jitter
        label_5=Label(root,text='Jitter:',width=15,font=("bold",10))
        label_5.place(x=0,y=130)
        entry_5=Entry(root)
        entry_5.place(x=125,y=130)
        linkEntries['jitter']=entry_5

        #Speedup
        label_6=Label(root,text='Speedup:',width=15,font=("bold",10))
        label_6.place(x=0,y=160)
        entry_6=Entry(root)
        entry_6.place(x=125,y=160)
        linkEntries['speedup']=entry_6

        bouton1=Button(root,text='OK',width=10,command=self.logInformationsLink)
        bouton1.place(x=80,y=200)
        bouton2=Button(root,text='Cancel',width=10,command = lambda:root.destroy())
        bouton2.place(x=210,y=200)

    def logInformationsLink(self):
        setLogLevel( 'info' )
        newLinkOptions={}
        self.links[self.selectedLink]['options']={}
        if(linkEntries['bw'].get() != ''):
            try:
                float(linkEntries['bw'].get())
                newLinkOptions['bw']=float(linkEntries['bw'].get())
                self.links[self.selectedLink]['options']['bw']=float(linkEntries['bw'].get())
            except ValueError:
                root=Toplevel()
                text1=Text(root,height=200,width=200)
                text1.config(state="normal")
                text1.insert(INSERT,'Bandwidth should be a float')
                text1.config(state='disabled')
                text1.pack()

        if(linkEntries['delay'].get() != ''):
            try:
                float(linkEntries['delay'].get())
                newLinkOptions['delay']=float(linkEntries['delay'].get())
                self.links[self.selectedLink]['options']['delay']=float(linkEntries['delay'].get())
            except ValueError:
                root=Toplevel()
                text1=Text(root,height=200,width=200)
                text1.config(state="normal")
                text1.insert(INSERT,'Delay should be a float')
                text1.config(state='disabled')
                text1.pack()

        if(linkEntries['loss'].get() != ''):
            try:
                float(linkEntries['loss'].get())
                newLinkOptions['loss']=float(linkEntries['loss'].get())
                self.links[self.selectedLink]['options']['loss']=float(linkEntries['loss'].get())
            except ValueError:
                root=Toplevel()
                text1=Text(root,height=200,width=200)
                text1.config(state="normal")
                text1.insert(INSERT,'Loss should be a float')
                text1.config(state='disabled')
                text1.pack()

        if(linkEntries['max_queue_size'].get() != ''):
            try:
                float(linkEntries['max_queue_size'].get())
                newLinkOptions['max_queue_size']=float(linkEntries['max_queue_size'].get())
                self.links[self.selectedLink]['options']['max_queue_size']=float(linkEntries['max_queue_size'].get())
            except ValueError:
                root=Toplevel()
                text1=Text(root,height=200,width=200)
                text1.config(state="normal")
                text1.insert(INSERT,'Max queue size should be a float')
                text1.config(state='disabled')
                text1.pack()

        if(linkEntries['jitter'].get() != ''):
            try:
                float(linkEntries['jitter'].get())
                newLinkOptions['jitter']=float(linkEntries['jitter'].get())
                self.links[self.selectedLink]['options']['jitter']=float(linkEntries['jitter'].get())
            except ValueError:
                root=Toplevel()
                text1=Text(root,height=200,width=200)
                text1.config(state="normal")
                text1.insert(INSERT,'Jitter should be a float')
                text1.config(state='disabled')
                text1.pack()

        #newLinkOptions['jitter']=linkEntries['jitter'].get()
        if(linkEntries['speedup'].get() != ''):
            try:
                float(linkEntries['speedup'].get())
                newLinkOptions['speedup']=float(linkEntries['speedup'].get())
                self.links[self.selectedLink]['options']['speedup']=float(linkEntries['speedup'].get())
            except ValueError:
                root=TopLevel()
                text1=Text(root,height=200,width=200)
                text1.config(state="normal")
                text1.insert(INSERT,'Speedup should be a float')
                text1.config(state='disabled')
                text1.pack()
        info('New link details for ' + '=' + str(self.links[self.selectedLink]['options']) + '\n')

    def change(self,*args):
        print("enableNetFlow"+str(var_2.get())+'\n')

    def change1(self,*args):
        print("enablesFlow"+str(var_3.get())+'\n')

    def change3(self,*args):
        listVariable['switchType']=var.get()
        #print("ListVariable['switchtype']="+str(listVariable['switchType']))


    def addListbox(self):
        listbox.insert(END,content.get())
        listEntries.append(content.get())
        #print("listEntries_addlistbox:"+str(listEntries))

    def switchProperties(self):
        global listEntries # contient external Interfaces
        listEntries=[]
        global listVariable
        listVariable={}
        global content
        content=StringVar()
        global listbox
        global var_2
        var_2=IntVar()
        global var_3
        var_3=IntVar()
        global var
        var=StringVar()
        Options=["Default","Open VSwitch Kernel Mode","Indigo Virtual Switch","Userspace Switch","Userspace Switch inNamespace"]
        fen = Toplevel()
        fen.geometry('500x500')

        #Switch Name
        label_1=Label(fen,text="Hostname :",width=20,font=("bold",10))
        label_1.place(x=0,y=10)
        var_1=StringVar()
        var_1.set(str(self.switchOptions[self.selectedNode]['nameSwitch']))
        entry_1=Entry(fen,textvariable=var_1)
        entry_1.place(x=130,y=10)
        listVariable['nameSwitch']=str(self.switchOptions[self.selectedNode]['nameSwitch'])

        #Switch number
        var1=self.switchOptions[self.selectedNode]['numSwitch']
        listVariable['numSwitch']=str(self.switchOptions[self.selectedNode]['numSwitch'])

        #External Interfaces
        label_9=Label(fen,text="External Interface :",width=20,font=("bold",10))
        label_9.place(x=290,y=10)
        bouton5=Button(fen,text="Add",command=self.addListbox)
        bouton5.place(x=440,y=8)
        label_10=Label(fen,text="External Interfaces")
        label_10.place(x=330,y=50)
        frame=Frame(fen, width=170, height=320) #background
        frame.place(x=320,y=80)
        entry_11=Entry(frame,textvariable=content)
        entry_11.pack()
        scroll= Scrollbar(frame)
        scroll.pack(side=RIGHT,fill=Y)
        listbox=Listbox(frame,yscrollcommand=scroll.set)
        listbox.pack()
        scroll.config(command=listbox.yview)

        #DPID
        label_2=Label(fen,text="DPID :",width=20,font=("bold",10))
        label_2.place(x=0,y=40)
        entry_2=Entry(fen)
        entry_2.place(x=110,y=40)
        listVariable["dpid"]=entry_2

        #EnableNetFlow
        label_2=Label(fen,text="Enable NetFlow :",width=20,font=("bold",10))
        label_2.place(x=0,y=70)
        bouton2=Checkbutton(fen,variable=var_2)
        bouton2.bind('<Button-1>',self.change)
        bouton2.place(x=130,y=70)

        #EnablesFlow
        label_3=Label(fen,text="Enable sFlow :",width=20,font=("bold",10))
        label_3.place(x=0,y=100)
        bouton3=Checkbutton(fen,variable=var_3)
        bouton3.bind('<Button-1>',self.change1)
        bouton3.place(x=130,y=100)

        #Switch Type
        label_4=Label(fen,text="Switch Type",width=20,font=("bold",10))
        label_4.place(x=0,y=130)
        var.set(Options[0])
        var.trace("w",self.change3)
        dropDownMenu=OptionMenu(fen,var,Options[0],Options[1],Options[2],Options[3],Options[4])
        dropDownMenu.place(x=130,y=130)

        #Controllers
        listVariable["controllers"]=self.switchOptions[self.selectedNode]['options']['controllers'] #controllers

        #IP address
        label_5=Label(fen,text="IP Address :",width=20,font=("bold",10))
        label_5.place(x=0,y=160)
        entry_3=Entry(fen)
        entry_3.place(x=130,y=160)
        listVariable["ipAddress"]=entry_3

        label_6=Label(fen,text="DPCTL port :",width=20,font=("bold",10))
        label_6.place(x=0,y=190)
        entry_4=Entry(fen)
        entry_4.place(x=130,y=190)
        listVariable['dpctlPort']=entry_4

        label_7=Label(fen,text="Start Command :",width=20,font=("bold",10))
        label_7.place(x=0,y=320)
        entry_5=Entry(fen)
        entry_5.place(x=140,y=320,width=350)
        listVariable['start']=entry_5

        label_8=Label(fen,text="Stop Command :",width=20,font=("bold",10))
        label_8.place(x=0,y=350)
        entry_6=Entry(fen)
        entry_6.place(x=140,y=350,width=350)
        listVariable['stop']=entry_6

        bouton10=Button(fen,text='OK',width=10,command=self.logInformationsSwitch)
        bouton10.place(x=200,y=420)
        bouton11=Button(fen,text='Cancel',width=10,command=lambda : fen.destroy())
        bouton11.place(x=350,y=420)

    def logInformationsSwitch(self):
        #c'est ici que toutes les modifications doivent etre faites
        setLogLevel('info')
        newSwitchOptions={}
        newSwitchOptions['hostname']=listVariable['nameSwitch']
        newSwitchOptions['number']=listVariable['numSwitch']
        newSwitchOptions['switchIP']=listVariable['ipAddress'].get()
        newSwitchOptions['dpctl']=listVariable['dpctlPort'].get()
        newSwitchOptions['dpid']=listVariable['dpid'].get()
        newSwitchOptions['switchType']=var.get()
        newSwitchOptions['sflow']=var_3.get()
        newSwitchOptions['netflow']=var_2.get()
        newSwitchOptions['controllers']=listVariable['controllers']
        newSwitchOptions['externalInterfaces']= listEntries
        newSwitchOptions['startCommand']=listVariable['start'].get()
        newSwitchOptions['stopCommand']=listVariable['stop'].get()
        self.switchOptions[self.selectedNode]['options']=newSwitchOptions
        info('New switch details for ' + str(newSwitchOptions['hostname']) + '=' + str(newSwitchOptions) + '\n')

    def changehost(self,*args):
        hostnames1['host0']=varhost.get()
        hostnodes1[0]=self.name_host[hostnames1['host0']]

    def changehost1(self,*args):
        hostnames1['host1']=varhost1.get()
        hostnodes1[1]=self.name_host[hostnames1['host1']]

    def changeNumber(self,*args):
        choosenNumber[0]=varnumber.get()

    def pingpacket(self):
        root=Toplevel()
        global choosenNumber
        choosenNumber=[1]
        numbers=[1]
        for i in range(2,21):
            numbers.append(i)

        global hostnodes1
        global hostnames1
        hostnames1={}

        global varnumber
        varnumber=StringVar()

        global varhost
        varhost=StringVar()

        global varhost1
        varhost1=StringVar()

        #le nom de tous les hotes
        name_hosts=[]
        for host in self.name_host.keys():
            name_hosts.append(host)

        hostnames1['host0']=name_hosts[0]
        hostnames1['host1']=name_hosts[0]

        hostnodes1=[self.name_host[hostnames1['host0']],self.name_host[hostnames1['host1']]]
        varhost.trace("w",self.changehost)
        varhost1.trace("w",self.changehost1)
        varnumber.trace("w",self.changeNumber)
        varhost.set(hostnames1['host0'])
        varhost1.set(hostnames1['host1'])
        varnumber.set('1')
        dropDownMenu=OptionMenu(root,varhost,*name_hosts)
        dropDownMenu.place(x=0,y=50)

        dropDownMenu1=OptionMenu(root,varhost1,*name_hosts)
        dropDownMenu1.place(x=60,y=50)

        dropDownMenu2=OptionMenu(root,varnumber,*numbers)
        dropDownMenu2.place(x=120,y=50)

        bouton=Button(root,text='OK',command=partial(self.pingpacket1,hostnames1,choosenNumber))
        bouton.place(x=180,y=50)

    def changeNode(self,*args):
        node[0]=varname.get()

    def node_info(self):
        global node
        root=Toplevel()
        root.geometry('380x170')
        helv36 = Font(family='Helvetica', size=10, weight='bold')
        label=Label(root,text='Nodes informations',font=helv36)
        label.place(x=135,y=0)
        label1=Label(root,text='Choose node',font=helv36)
        label1.place(x=155,y=30)
        link_names=()
        names = tuple(self.names)
        for link in self.links.keys():
            info_link=('Link between ' + str(self.links[link]['src']) + ' and ' + str(self.links[link]['dest']),)
            link_names=link_names+info_link

        nodes_links = names+link_names
        menuwidth = len(max(nodes_links,key=len))
        node=[names[0]]
        global varname
        varname=StringVar()
        varname.set(names[0])
        varname.trace("w",self.changeNode)
        dropdownmenu=OptionMenu(root,varname,*nodes_links)
        dropdownmenu.config(width=menuwidth)
        dropdownmenu.grid()
        dropdownmenu.place(x=95,y=60)
        bouton = Button(root,text='OK',command=self.node_info1)
        bouton.place(x=170,y=110)

    def node_info1(self):
        #cas switch
        root=Toplevel()
        text1=Text(root,height=200,width=200)
        text1.config(state="normal")

        for switch in self.switchOptions.keys():
            item=self.widgetToItem[switch]
            name_node=self.itemToName[item]
            if(node[0]==name_node):
                text1.insert(INSERT,'Switch Name : ' + self.switchOptions[switch]['options']['hostname']+'\n')
                text1.insert(INSERT,'Switch Type : ' + self.switchOptions[switch]['options']['switchType']+'\n')

                if(self.switchOptions[switch]['options']['sflow'] == 0 ):
                    text1.insert(INSERT,'sFlow : Not Checked ' + '\n')
                else:
                    text1.insert(INSERT,'sFlow : Checked ' + '\n')

                if(self.switchOptions[switch]['options']['netflow'] == 0 ):
                    text1.insert(INSERT,'netFlow : Not Checked ' + '\n')
                else:
                    text1.insert(INSERT,'netFlow : Checked ' + '\n')

                if(self.switchOptions[switch]['options']['controllers'] != [] ):
                    text1.insert(INSERT,'Controllers : ')
                    text1.insert(INSERT,self.switchOptions[switch]['options']['controllers'])
                    text1.insert(INSERT,'\n')

                if(self.switchOptions[switch]['options']['switchIP']!=''):
                    text1.insert(INSERT,'IP Address : ' + self.switchOptions[switch]['options']['switchIP']+'\n')

                if(self.switchOptions[switch]['options']['dpid']!=''):
                    text1.insert(INSERT,'dpid : ' + self.switchOptions[switch]['options']['dpid']+'\n')

                if(self.switchOptions[switch]['options']['dpctl']!=''):
                    text1.insert(INSERT,'dpctl : ' + self.switchOptions[switch]['options']['dpctl']+'\n')

                if(self.switchOptions[switch]['options']['startCommand']!=''):
                    text1.insert(INSERT,'start Command : ' + self.switchOptions[switch]['options']['startCommand']+'\n')

                if(self.switchOptions[switch]['options']['stopCommand']!=''):
                    text1.insert(INSERT,'stop Command : ' + self.switchOptions[switch]['options']['stopCommand']+'\n')

                if(self.switchOptions[switch]['options']['externalInterfaces'] != [] ):
                    text1.insert(INSERT,'External Interfaces : ')
                    text1.insert(INSERT,self.switchOptions[switch]['options']['externalInterfaces'])
                    text1.insert(INSERT,'\n')

                text1.config(state='disabled')
                text1.pack()
                return

        #cas host
        for host in self.hostOptions.keys():
            item=self.widgetToItem[host]
            name_node=self.itemToName[item]
            if(node[0]==name_node):
                #print(self.hostOptions[host])
                text1.insert(INSERT,'host Number : ' + str(self.hostOptions[host]['numhost'])+'\n')
                text1.insert(INSERT,'hostname : ' + self.hostOptions[host]['hostname']+'\n')
                text1.insert(INSERT,'Sched : ' + self.hostOptions[host]['options']['sched']+'\n')
                #print(self.hostOptions[host]['options']['cpu'])

                if(self.hostOptions[host]['options']['cpu']!=''):
                     #print('we are in cpu')
                     text1.insert(INSERT,'CPU : ' + self.hostOptions[host]['options']['cpu']+'\n')

                if(self.hostOptions[host]['options']['ip']!=''):
                    #print('we are in ip')
                    text1.insert(INSERT,'IP Address : ' + self.hostOptions[host]['options']['ip']+'\n')

                if(self.hostOptions[host]['options']['defaultRoute']!=''):
                    #print('we are in default route')
                    text1.insert(INSERT,'Default Route : ' + self.hostOptions[host]['options']['defaultRoute']+'\n')

                if(self.hostOptions[host]['options']['cores']!=''):
                    #print('we are in cores')
                    text1.insert(INSERT,'Cores : ' + self.hostOptions[host]['options']['cores']+'\n')

                if(self.hostOptions[host]['options']['startCommand']!=''):
                    #print('we are in start command')
                    text1.insert(INSERT,'start Command : ' + self.hostOptions[host]['options']['startCommand']+'\n')

                if(self.hostOptions[host]['options']['stopCommand']!=''):
                    #print('we are in stop command')
                    text1.insert(INSERT,'stop Command : ' + self.hostOptions[host]['options']['stopCommand']+'\n')

                if(self.hostOptions[host]['options']['vlanInterfaces']!=[]):
                    #print('we are in vlan interface')
                    text1.insert(INSERT,'VLAN Interfaces : ')
                    text1.insert(INSERT,self.hostOptions[host]['options']['vlanInterfaces'])
                    text1.insert(INSERT,'\n')

                if(self.hostOptions[host]['options']['privateDirectory']!=[]):
                    #print('we are in private directories')
                    text1.insert(INSERT,'Private Directories : ')
                    text1.insert(INSERT,self.hostOptions[host]['options']['privateDirectory'])
                    text1.insert(INSERT,'\n')

                if(self.hostOptions[host]['options']['externalInterfaces']!=[]):
                    #print('we are in external interfaces')
                    text1.insert(INSERT,'External Interfaces : ')
                    text1.insert(INSERT,self.hostOptions[host]['options']['externalInterfaces'])
                    text1.insert(INSERT,'\n')

                text1.config(state='disabled')
                text1.pack()
                return

        #cas Controller
        for controller in self.controllerOptions.keys():
            item=self.widgetToItem[controller]
            name_node=self.itemToName[item]
            if(node[0]==name_node):
                #text1.insert(INSERT,self.controllerOptions[controller])
                text1.insert(INSERT,'Controller Name : ' + str(self.controllerOptions[controller]['hostname'])+'\n')
                text1.insert(INSERT,'Remote Port : ' + str(self.controllerOptions[controller]['options']['remotePort'])+'\n')
                text1.insert(INSERT,'Controller Protocol : ' + str(self.controllerOptions[controller]['options']['controllerProtocol'])+'\n')
                text1.insert(INSERT,'Remote IP : ' + str(self.controllerOptions[controller]['options']['remoteIP'])+'\n')
                text1.insert(INSERT,'Controller Type : ' + str(self.controllerOptions[controller]['options']['controllerType'])+'\n')
                text1.config(state='disabled')
                text1.pack()
                return

        #cas legacyswitch
        for lswitch in self.legacySwitchOptions.keys():
            item=self.widgetToItem[lswitch]
            name_node=self.itemToName[item]
            if(node[0]==name_node):
                text1.insert(INSERT,'Legacy Switch Name : ' + self.legacySwitchOptions[lswitch]['name'] + '\n')
                text1.insert(INSERT,'Legacy Switch Number : ' + str(self.legacySwitchOptions[lswitch]['number']) + '\n')
                text1.insert(INSERT,'Switch Type : ' + self.legacySwitchOptions[lswitch]['options']['switchType']+'\n')
                text1.config(state='disabled')
                text1.pack()
                return

        #cas lrouter
        for lrouter in self.legacyRouterOptions.keys():
            item=self.widgetToItem[lrouter]
            name_node=self.itemToName[item]
            if(node[0]==name_node):
                text1.insert(INSERT,'Legacy Router Name : ' + self.legacyRouterOptions[lrouter]['name'] + '\n')
                text1.insert(INSERT,'Legacy Router Number : ' + str(self.legacyRouterOptions[lrouter]['number']) + '\n')
                text1.insert(INSERT,'Switch Type : ' + self.legacyRouterOptions[lrouter]['options']['switchType']+'\n')
                text1.config(state='disabled')
                text1.pack()
                return

        for link in self.links.keys():
            #print('self.links')
            #print(self.links)
            link_info = 'Link between ' + str(self.links[link]['src']) + ' and ' + str(self.links[link]['dest'])
            if(node[0]==link_info):
                #print('we are in self.links.keys')
                text1.insert(INSERT,"Link source : " + str(self.links[link]['src']) + '\n')
                text1.insert(INSERT,"Link destination : " + str(self.links[link]['dest']) + '\n')
                text1.insert(INSERT,"Link type : " + str(self.links[link]['type']) + '\n')

                if(self.links[link]['type'] == 'data' and self.links[link]['options'] != {} and self.links[link]['options']!= None):
                    if('loss' in self.links[link]['options'].keys()):
                        text1.insert(INSERT,'Loss : ' + str(self.links[link]['options']['loss']) + '\n')

                    if('jitter' in self.links[link]['options'].keys()):
                        text1.insert(INSERT,'Jitter : ' + str(self.links[link]['options']['jitter']) + '\n')

                    if('speedup' in self.links[link]['options'].keys()):
                        text1.insert(INSERT,'Speedup : ' + str(self.links[link]['options']['speedup']) + '\n')

                    if('delay' in self.links[link]['options'].keys()):
                        text1.insert(INSERT,'Delay : ' + str(self.links[link]['options']['delay'])+ '\n')

                    if('bw' in self.links[link]['options'].keys()):
                        text1.insert(INSERT,'Bandwidth : ' + str(self.links[link]['options']['bw'])+ '\n')

                    if('max_queue_size' in self.links[link]['options'].keys()):
                        text1.insert(INSERT,'Max queue size : ' + str(self.links[link]['options']['max_queue_size'])+ '\n')

                text1.config(state='disabled')
                text1.pack()
                return

    def logInformationsPreferences(self):
        setLogLevel('info')
        newPrefOptions={}
        newPrefOptions['dpctl']=variables['dpctl'].get()
        newPrefOptions['sflow']={}
        newPrefOptions['sflow']['sflowPolling']=variables['sFlowPolling'].get()
        newPrefOptions['sflow']['sflowHeader']=variables['sFlowHeader'].get()
        newPrefOptions['sflow']['sflowTarget']=variables['sFlowTarget'].get()
        newPrefOptions['sflow']['sflowSampling']=variables['sFlowSampling'].get()
        newPrefOptions['openFlowVersions']={}
        newPrefOptions['openFlowVersions']['ovsOf10']=ovsOf10.get()
        newPrefOptions['openFlowVersions']['ovsOf11']=ovsOf11.get()
        newPrefOptions['openFlowVersions']['ovsOf12']=ovsOf12.get()
        newPrefOptions['openFlowVersions']['ovsOf13']=ovsOf13.get()
        newPrefOptions['ipBase']=variables['ipBase'].get()
        newPrefOptions['terminalType']=variables['terminalType'].get()
        newPrefOptions['switchType']=variables['switchType'].get()
        newPrefOptions['netflow']={}
        newPrefOptions['netflow']['nflowTarget']=variables['nFlowTarget'].get()
        newPrefOptions['netflow']['nflowTimeout']=variables['nFlowTimeout'].get()
        newPrefOptions['netflow']['nflowAddId']=nFlowAddId.get()
        newPrefOptions['startCLI']=varStartCLI.get()
        #print("varStartCLI"+str(newPrefOptions['startCLI']))
        self.preferences=newPrefOptions
        #print("we are in log Informations preferences")
        #print(self.preferences)
        info('New Prefs ' + '=' + str(newPrefOptions) + '\n')

    def changeTerminalType(self,*args):
        variables['terminalType']=varTerminalType

    def changeSwitchType(self,*args):
        variables['switchType']=varSwitchType

    def setPreferences(self):
        optionsTerminal=['xterm','gterm']
        optionsSwitch=["Open vSwitch Kernel Mode","Indigo Virtual Switch","Userspace Switch","Userspace Switch inNamespace"]
        global varTerminalType
        varTerminalType=StringVar()
        global varStartCLI
        varStartCLI=IntVar()
        global varSwitchType
        varSwitchType=StringVar()
        global variables
        variables={}
        global ovsOf10
        ovsOf10=IntVar()
        ovsOf10.set(1)
        global ovsOf11
        ovsOf11=IntVar()
        global ovsOf12
        ovsOf12=IntVar()
        global ovsOf13
        ovsOf13=IntVar()
        global nFlowAddId
        nFlowAddId=IntVar()
        root=Toplevel()
        root.geometry("770x390")
        root.title("Preferences")

        #IP base
        label_1=Label(root,text="IP base :",width=10,font=("bold",10))
        label_1.place(x=0,y=10)
        var_1=StringVar()
        var_1.set("10.0.0.0/8")
        entry_1=Entry(root,textvariable=var_1)
        entry_1.place(x=150,y=10)
        variables['ipBase']=entry_1

        #terminalType Type A revoir
        label_2=Label(root,text="Default Terminal:",width=17,font=("bold",10))
        label_2.place(x=0,y=40)
        varTerminalType.set(optionsTerminal[0])
        variables['terminalType']=varTerminalType
        varTerminalType.trace("w",self.changeTerminalType)
        dropDownMenu=OptionMenu(root,varTerminalType,optionsTerminal[0],optionsTerminal[1])
        dropDownMenu.place(x=150,y=40)

        #CLI
        label_3=Label(root,text="Start CLI :",width=10,font=("bold",10))
        label_3.place(x=0,y=70)
        bouton2=Checkbutton(root,variable=varStartCLI)
        bouton2.place(x=150,y=70)

        #SwitchType
        label_4=Label(root,text="Default Switch :",width=15,font=("bold",10))
        label_4.place(x=0,y=100)
        varSwitchType.set(optionsSwitch[0])
        variables['switchType']=varSwitchType
        varSwitchType.trace("w",self.changeSwitchType)
        dropDownMenu1=OptionMenu(root,varSwitchType,optionsSwitch[0],optionsSwitch[1],optionsSwitch[2],optionsSwitch[3])
        dropDownMenu1.place(x=150,y=100)

        #OpenVSwitch
        frame1=LabelFrame(root,width=350, height=150, text="Open vSwitch")
        frame1.place(x=10,y=130)

        #OpenFlow 1.0
        label_5=Label(frame1,text="OpenFlow 1.0:")
        label_5.place(x=0,y=10)
        bouton3=Checkbutton(frame1,variable=ovsOf10)
        bouton3.place(x=100,y=10)

        #OpenFlow 1.1
        label_6=Label(frame1,text="OpenFlow 1.1:")
        label_6.place(x=0,y=40)
        bouton4=Checkbutton(frame1,variable=ovsOf11)
        bouton4.place(x=100,y=40)

        #OpenFlow 1.2
        label_7=Label(frame1,text="OpenFlow 1.2:")
        label_7.place(x=0,y=70)
        bouton5=Checkbutton(frame1,variable=ovsOf12)
        bouton5.place(x=100,y=70)

        #OpenFlow 1.3
        label_8=Label(frame1,text="OpenFlow 1.3:")
        label_8.place(x=0,y=100)
        bouton6=Checkbutton(frame1,variable=ovsOf13)
        bouton6.place(x=100,y=100)

        #dpctl port
        label_9=Label(root,text='dpctl port:')
        label_9.place(x=40,y=290)
        entry_2=Entry(root)
        entry_2.place(x=160,y=290)
        variables['dpctl']=entry_2

        frame2=LabelFrame(root,width=350, height=150, text="sFlow Profile for Open vSwitch")
        frame2.place(x=400,y=10)

        #Target
        label_10=Label(frame2,text='Target:')
        label_10.place(x=0,y=10)
        entry_3=Entry(frame2)
        entry_3.place(x=60,y=10)
        variables['sFlowTarget']=entry_3

        #Sampling
        label_11=Label(frame2,text='Sampling:')
        label_11.place(x=0,y=40)
        var_7=StringVar()
        var_7.set("400")
        entry_4=Entry(frame2,textvariable=var_7)
        entry_4.place(x=70,y=40)
        variables['sFlowSampling']=entry_4

        #Header
        label_12=Label(frame2,text='Header:')
        label_12.place(x=0,y=70)
        var_3=StringVar()
        var_3.set("128")
        entry_5=Entry(frame2,textvariable=var_3)
        entry_5.place(x=60,y=70)
        variables['sFlowHeader']=entry_5

        #Polling
        label_13=Label(frame2,text='Polling:')
        label_13.place(x=0,y=100)
        var_4=StringVar()
        var_4.set("30")
        entry_6=Entry(frame2,textvariable=var_4)
        entry_6.place(x=60,y=100)
        variables['sFlowPolling']=entry_6

        frame3=LabelFrame(root,width=350, height=160, text="NetFlow Profile for Open vSwitch")
        frame3.place(x=400,y=170)
        label_14=Label(frame3,text='Target:')
        label_14.place(x=70,y=10)
        entry_7=Entry(frame3)
        entry_7.place(x=120,y=10)
        variables['nFlowTarget']=entry_7

        label_15=Label(frame3,text='Active Timeout:')
        label_15.place(x=20,y=40)
        var_5=StringVar()
        var_5.set("600")
        entry_8=Entry(frame3,textvariable=var_5)
        entry_8.place(x=130,y=40)
        variables['nFlowTimeout']=entry_8

        label_16=Label(frame3,text='Add ID to Interface:')
        label_16.place(x=0,y=70)
        bouton7=Checkbutton(frame3,variable=nFlowAddId)
        bouton7.place(x=135,y=70)

        bouton8=Button(root,text="OK",width=10,command=self.logInformationsPreferences)
        bouton8.place(x=280,y=345)
        bouton9=Button(root,text="Cancel",width=10,command = lambda : root.destroy())
        bouton9.place(x=400,y=345)
        #root.mainloop()

    #Placer un bouton sur le canevas
    def canvasHandle(self,event):
        x1=event.x
        y1=event.y
        if (self.activeButton == 'Switch'):
            #bouton1=Button(self.canvas,image=self.images['Switch'])
            self.switchNumber+=1
            name_switch='s'+str(self.switchNumber) #s1
            bouton1=Button(self.canvas,image=self.images['Switch'],text=name_switch,compound='top',bg='white')
            self.switchOptions[bouton1]={}
            self.switchOptions[bouton1]['numSwitch']=self.switchNumber
            self.switchOptions[bouton1]['nameSwitch']=name_switch
            #self.switchOptions[bouton1]['controllers']=[]
            self.switchOptions[bouton1]['options']={"controllers": [],"hostname": name_switch,"nodenum":self.switchNumber,"switchType":"Default",'stopCommand':'','sflow':0,'switchIP':'','dpid':'','dpctl':'','startCommand':'','netflow':0,'externalInterfaces':[]}
            self.name_switch.append(name_switch)
            id1=self.canvas.create_window((x1,y1),anchor='center',window=bouton1,tags='Switch')
            self.widgetToItem[bouton1]=id1
            self.itemToWidget[id1]=bouton1
            self.itemToName[id1]=name_switch
            self.buttons_canevas[name_switch]=bouton1
            self.make_draggable_switch(self.buttons_canevas[name_switch])
            self.nb_widget_canevas+=1
            self.list_buttons['Switch'].config(relief="raised")
            self.names.append(name_switch)
            self.activeButton=None
        elif(self.activeButton == 'Host'):
            #bouton2=Button(self.canvas,image=self.images['Host'])
            self.hostNumber+=1
            #bouton2=Button(self.canvas,image=self.images['Host'],text=str(self.hostNumber),compound='top')
            name_host='h'+str(self.hostNumber) #h1
            bouton2=Button(self.canvas,image=self.images['Host'],text=name_host,bg='white',compound='top')
            self.hostOptions[bouton2]={}
            #self.hostOptions[bouton2]['sched']='host'
            self.hostOptions[bouton2]['numhost']=self.hostNumber
            self.hostOptions[bouton2]['hostname']=name_host
            self.hostOptions[bouton2]['options']={}
            self.hostOptions[bouton2]['options']={'hostname':name_host,"nodeNum":self.hostNumber,"sched":"host",'stopCommand':'','externalInterfaces':[],'ip':'','privateDirectory':[],'nodeNum':self.hostNumber,'vlanInterfaces':[],'cores':'','startCommand':'','cpu':'','defaultRoute':''}
            id2=self.canvas.create_window((x1,y1),anchor='center',window=bouton2,tags='host')
            self.itemToName[id2]=name_host
            self.widgetToItem[bouton2]=id2
            self.itemToWidget[id2]=bouton2
            self.buttons_canevas[name_host]=bouton2
            self.make_draggable_host(self.buttons_canevas[name_host])
            self.nb_widget_canevas+=1
            self.list_buttons['Host'].config(relief="raised")
            self.names.append(name_host)
            self.activeButton=None
        elif(self.activeButton == 'Controller'):
            #bouton3=Button(self.canvas,image=self.images['Controller'])
            self.controllerNumber+=1
            name_controller='c'+str(self.controllerNumber)
            bouton3=Button(self.canvas,image=self.images['Controller'],bg='white',text=name_controller,compound='top')
            id3=self.canvas.create_window((x1,y1),anchor='center',window=bouton3,tags='Controller')
            self.controllerOptions[bouton3]={}
            #self.controllerOptions[bouton3]['numController']=self.controllerNumber
            self.controllerOptions[bouton3]['hostname']=name_controller
            self.controllerOptions[bouton3]['options']={'hostname':name_controller,'remotePort':6633,'controllerType':'OpenFlow Reference','controllerProtocol':'tcp','remoteIP':'127.0.0.1'}
            self.widgetToItem[bouton3]=id3
            self.itemToWidget[id3]=bouton3
            self.itemToName[id3]=name_controller
            self.buttons_canevas[name_controller]=bouton3
            self.make_draggable_controller(self.buttons_canevas[name_controller])
            self.nb_widget_canevas+=1
            self.list_buttons['Controller'].config(relief="raised")
            self.names.append(name_controller)
            self.activeButton=None
        elif(self.activeButton == 'LegacySwitch'):
            self.switchNumber+=1
            name_legacySwitch = 's' + str(self.switchNumber)
            bouton4=Button(self.canvas,image=self.images['LegacySwitch'],text=name_legacySwitch,bg='white',compound='top')
            self.buttons_canevas[name_legacySwitch]=bouton4
            self.legacySwitchOptions[bouton4]={}
            self.legacySwitchOptions[bouton4]['name']=name_legacySwitch
            self.legacySwitchOptions[bouton4]['number']=self.switchNumber
            self.legacySwitchOptions[bouton4]['options']={'num':self.switchNumber,'hostname':name_legacySwitch,'switchType':'LegacySwitch'}
            id4=self.canvas.create_window((x1,y1),anchor='center',window=bouton4,tags='LegacySwitch')
            self.itemToName[id4]=name_legacySwitch
            self.widgetToItem[bouton4]=id4
            self.itemToWidget[id4]=bouton4
            self.names.append(name_legacySwitch)
            self.make_draggable_legacySwitch(bouton4)
            self.nb_widget_canevas+=1
            self.list_buttons['LegacySwitch'].config(relief='raised')
            self.activeButton=None
        elif(self.activeButton == 'LegacyRouter'):
            #print('we are in legacyRouter')
            self.switchNumber+=1
            name_legacyRouter = 'r' + str(self.switchNumber)
            bouton5=Button(self.canvas,image=self.images['LegacyRouter'],text=name_legacyRouter,bg='white',compound='top')
            self.buttons_canevas[name_legacyRouter]=bouton5
            self.legacyRouterOptions[bouton5]={}
            self.legacyRouterOptions[bouton5]['name']=name_legacyRouter
            self.legacyRouterOptions[bouton5]['number']=self.switchNumber
            self.legacyRouterOptions[bouton5]['options']={'num':self.switchNumber,'hostname':name_legacyRouter,'switchType':'LegacyRouter'}
            id5=self.canvas.create_window((x1,y1),anchor='center',window=bouton5,tags='LegacyRouter')
            self.itemToName[id5]=name_legacyRouter
            self.widgetToItem[bouton5]=id5
            self.itemToWidget[id5]=bouton5
            self.names.append(name_legacyRouter)
            self.make_draggable_legacyRouter(bouton5)
            self.nb_widget_canevas+=1
            self.list_buttons['LegacyRouter'].config(relief='raised')
            self.activeButton=None

    def saveTopology(self):
        fileTypes = [("Mininet Topology","*.mn"),("All Files",'*')]
        result = tkFileDialog.asksaveasfilename(filetypes=fileTypes,title="Save topology")
        savingSwitches=[]
        savinghosts=[]
        savinglinks=[]
        savingControllers=[]
        dictionary={}
        for item in self.widgetToItem.values():
            tag = self.canvas.gettags(item)
            x,y = self.canvas.coords(item)
            widget=self.itemToWidget[item]
            if('Switch' in tag):
                switchNum=self.switchOptions[widget]['numSwitch']
                switchName=self.switchOptions[widget]['nameSwitch']
                savingSwitch={'number':str(switchNum),'x':str(x),'y':str(y),'opts':self.switchOptions[widget]['options']}
                savingSwitches.append(savingSwitch)
            elif('host' in tag):
                hostNum=self.hostOptions[widget]['numhost']
                savinghost={'number':str(hostNum),'x':str(x),'y':str(y),'opts':self.hostOptions[widget]['options']}
                savinghosts.append(savinghost)
            elif('LegacySwitch' in tag):
                legacySwitchNum=self.legacySwitchOptions[widget]['number']
                legacySwitchName=self.legacySwitchOptions[widget]['name']
                savingLegacySwitch={'number':str(legacySwitchNum),'x':str(x),'y':str(y),'opts':self.legacySwitchOptions[widget]['options']}
                savingSwitches.append(savingLegacySwitch)
            elif('LegacyRouter' in tag):
                legacyRouterNum=self.legacyRouterOptions[widget]['number']
                legacyRouterName=self.legacyRouterOptions[widget]['name']
                savingLegacyRouter={'number':str(legacyRouterNum),'x':str(x),'y':str(y),'opts':self.legacyRouterOptions[widget]['options']}
                savingSwitches.append(savingLegacyRouter)
            elif('Controller' in tag ):
                savingController={'x':str(x),'y':str(y),'opts':self.controllerOptions[widget]['options'] }
                savingControllers.append(savingController)
        dictionary['hosts']=savinghosts
        dictionary['switches']=savingSwitches
        dictionary['controllers']=savingControllers
        dictionary['application']=self.preferences

        for link in self.links.keys():
            options={}
            src = self.links[link]['src']
            target = self.links[link]['dest']
            #print("target save topology: "+str(target))
            if(self.links[link]['options'] == None):
                options={}
            savingLink={'src':src,'dest':target,'options':options}
            if (self.links[link]['type'] == 'data'):
                savinglinks.append(savingLink)

        dictionary['links']=savinglinks
        dictionary['application']=self.preferences

        f = open(result,'w')
        f.write(json.dumps(dictionary, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()

    def run(self):
        for bouton in self.list_buttons.values():
            bouton.config(state='disabled')
        self.start()

    def convertJsonUnicode(self, text):
        "Some part of Mininet don't like Unicode"
        if isinstance(text, dict):
            return {self.convertJsonUnicode(key): self.convertJsonUnicode(value) for key, value in text.items()}
        elif isinstance(text, list):
            return [self.convertJsonUnicode(element) for element in text]
        elif isinstance(text, unicode):
            return text.encode('utf-8')
        else:
            return text

    def loadTopology(self):
        fileTypes = [("Mininet Topology","*.mn"),("All Files",'*')]
        f=tkFileDialog.askopenfile(filetypes=fileTypes,title="Open file",mode='r')
        self.nvTopology()
        topologyLoaded=self.convertJsonUnicode(json.load(f))

        #load hosts
        hosts=topologyLoaded['hosts']
        if (len(hosts)!=0):
            for i in range(0,len(hosts)):
                nodeNum = hosts[i]['number']
                hostname= 'h'+str(nodeNum)
                x= hosts[i]['x']
                y=hosts[i]['y']
                self.hostNumber+=1
                icon = Button(self.canvas,image=self.images['Host'])
                item = self.canvas.create_window(x,y,anchor='c',window=icon,tags='host')
                self.widgetToItem[icon]=item
                self.itemToWidget[item]=icon
                self.nameToItem[hostname]=item;
                self.itemToName[item]=hostname
                self.names.append(hostname)
                self.make_draggable_host(icon)
                self.buttons_canevas[hostname]=icon
                self.hostOptions[icon]={}
                self.hostOptions[icon]['numhost']=self.hostNumber
                self.hostOptions[icon]['hostname']=hostname
                self.hostOptions[icon]['options']=hosts[i]['opts']

        #load controllers
        controllers=topologyLoaded['controllers']
        if(len(controllers)!=0):
            for j in range(0,len(controllers)):
                options=controllers[j]['opts']
                controller_name=options['hostname']
                x2=controllers[j]['x']
                y2=controllers[j]['y']
                self.controllerNumber+=1
                icon2=Button(self.canvas,image=self.images['Controller'])
                item2=self.canvas.create_window(x2,y2,anchor='c',window=icon2,tags='Controller')
                self.buttons_canevas[controller_name]=icon2
                self.widgetToItem[icon2]=item2
                self.itemToWidget[item2]=icon2
                self.names.append(controller_name)
                self.itemToName[item2]=controller_name
                self.make_draggable_controller(icon2)
                self.nameToItem[controller_name]=item2
                self.controllerOptions[icon2]={}
                self.controllerOptions[icon2]['hostname']=options['hostname']
                self.controllerOptions[icon2]['options']=options

        #load switches
        switches=topologyLoaded['switches']
        if(len(switches)!=0):
            for i in range(0,len(switches)):
                switch_option=switches[i]['opts']
                if(switch_option['switchType'] != 'LegacySwitch' and switch_option['switchType'] != 'LegacyRouter'):
                    switchNum=switches[i]['number']
                    switchName='s'+str(switchNum)
                    switch_option=switches[i]['opts']
                    x1=switches[i]['x']
                    y1=switches[i]['y']
                    self.switchNumber+=1
                    icon1 = Button(self.canvas,image=self.images['Switch'])
                    item1=self.canvas.create_window(x1,y1,anchor='c',window=icon1,tags='Switch')
                    self.itemToName[item1]=switchName
                    self.widgetToItem[icon1]=item1
                    self.itemToWidget[item1]=icon1
                    self.make_draggable_switch(icon1)
                    self.buttons_canevas[switchName]=icon1
                    self.names.append(switchName)
                    self.nameToItem[switchName]=item1;
                    self.switchOptions[icon1]={}
                    self.switchOptions[icon1]['numSwitch']=switchNum
                    self.switchOptions[icon1]['nameSwitch']=switchName
                    self.switchOptions[icon1]['options']=switches[i]['opts']

                # create links to controllers
                #if (switch_option['switchType'] != 'LegacyRouter' and switch_option['switchType'] != 'LegacySwitch'):
                    controllers=switch_option['controllers']   #list of controller
                    if(len(controllers)!=0):
                        for controller in controllers:
                            controller_item = self.nameToItem[controller]
                            dx, dy = self.canvas.coords(controller_item)
                            self.link = self.canvas.create_line(float(x1),float(y1),dx,dy,width=4,fill='red',dash=(6, 4, 2, 4),tag='link')
                            self.canvas.itemconfig(self.link,tags=self.canvas.gettags(self.link)+('control',))
                            self.liens.append(self.link)
                            self.links[self.link]={}
                            self.links[self.link]['src']=switchName
                            self.links[self.link]['dest']=controller
                            self.links[self.link]['type']='control'
                            self.ControlLinkBindings()
                            self.link = self.linkWidget = None

        #load legacySwitch
        switches=topologyLoaded['switches']
        if(len(switches)!=0):
            for i in range(0,len(switches)):
                options_switch=switches[i]['opts']
                #print(options_switch)
                if (options_switch['switchType'] == 'LegacySwitch'):
                    self.switchNumber+=1
                    legacyswitch_name = options_switch['hostname']
                    x3=switches[i]['x']
                    y3=switches[i]['y']
                    icon3=Button(self.canvas,image=self.images['LegacySwitch'])
                    item3=self.canvas.create_window(x3,y3,anchor='c',window=icon3,tags='LegacySwitch')
                    self.widgetToItem[icon3]=item3
                    self.itemToWidget[item3]=icon3
                    self.names.append(legacyswitch_name)
                    self.itemToName[item3]=options_switch['hostname']
                    self.buttons_canevas[legacyswitch_name]=icon3
                    self.make_draggable_legacySwitch(icon3)
                    self.nameToItem[options_switch['hostname']]=item3
                    self.legacySwitchOptions[icon3]={}
                    self.legacySwitchOptions[icon3]['name']=options_switch['hostname']
                    self.legacySwitchOptions[icon3]['number']=options_switch['num']
                    self.legacySwitchOptions[icon3]['options']=options_switch

        #load legacyRouter
        switches=topologyLoaded['switches']
        if(len(switches)!=0):
            for i in range(0,len(switches)):
                options_switch1=switches[i]['opts']
                if (options_switch1['switchType'] == 'LegacyRouter'):
                    self.switchNumber+=1
                    x4=switches[i]['x']
                    y4=switches[i]['y']
                    legacyrouter_name=options_switch1['hostname']
                    icon4=Button(self.canvas,image=self.images['LegacyRouter'])
                    item4=self.canvas.create_window(x4,y4,anchor='c',window=icon4,tags='LegacyRouter')
                    self.buttons_canevas[legacyrouter_name]=icon4
                    self.widgetToItem[icon4]=item4
                    self.itemToWidget[item4]=icon4
                    self.names.append(legacyrouter_name)
                    self.itemToName[item4]=options_switch1['hostname']
                    self.make_draggable_legacyRouter(icon4)
                    self.nameToItem[options_switch1['hostname']]=item4
                    self.legacySwitchOptions[icon3]={}
                    self.legacySwitchOptions[icon3]['name']=options_switch1['hostname']
                    self.legacySwitchOptions[icon3]['number']=options_switch1['num']
                    self.legacySwitchOptions[icon3]['options']=options_switch1

        #load Links
        links=topologyLoaded['links']
        #print('nameToItem'+str(self.nameToItem))
        #print('links'+str(links))
        if(len(links)!=0):
             for i in range(0,len(links)):
                 src = links[i]['src'] #nom de SRC
                 dst=links[i]['dest'] #nom de DEST
                 #print('item_src'+str(self.nameToItem[src]))
                 #print('item_dest'+str(self.nameToItem[dst]))
                 srcx,srcy=self.canvas.coords(self.nameToItem[src]); #coordonnées de la source
                 destx,desty=self.canvas.coords(self.nameToItem[dst]);
                 self.link=self.canvas.create_line(srcx,srcy,destx,desty,width=4,fill='blue',tag='link')
                 self.canvas.itemconfig(self.link,tags=self.canvas.gettags(self.link)+('data',))
                 self.links[self.link]={}
                 self.links[self.link]['options']={}
                 self.links[self.link]['src']=src
                 self.links[self.link]['dest']=dst
                 self.links[self.link]['type']='data'
                 #print('links[i][options] = ' + str(links[i]['options']))
                 self.links[self.link]['options']=links[i]['options']
                 self.DataLinkBindings()
                 self.liens.append(self.link)
                 self.link=None
                 self.linkWidget=None

        f.close()

    def canvasx( self, x_root ):
        return self.canvas.canvasx( x_root ) - self.canvas.winfo_rootx()

    def canvasy( self, y_root ):
        return self.canvas.canvasy( y_root ) - self.canvas.winfo_rooty()

    def findObject(self,x,y):
        items = self.canvas.find_overlapping(x,y,x,y)
        if len(items) == 0:
            return
        else:
            return items[0]

    def createLink(self,event):
        w = event.widget
        item = self.widgetToItem[w]
        x, y = self.canvas.coords(item)
        self.coordonnees["i0"]=x
        self.coordonnees["j0"]=y
        self.link = self.canvas.create_line(x,y,x,y,width=4,fill='blue',tag='link')
        self.links[self.link]={}
        tags = self.canvas.gettags(item)
        if ('Switch' in tags):
            self.links[self.link]['src']=self.switchOptions[w]['nameSwitch']
        elif('host' in tags):
            self.links[self.link]['src']=self.hostOptions[w]['hostname']
        elif('Controller' in tags):
            self.links[self.link]['src']=self.controllerOptions[w]['hostname']
        elif('LegacyRouter' in tags):
            self.links[self.link]['src']=self.legacyRouterOptions[w]['name']
        elif('LegacySwitch' in tags):
            self.links[self.link]['src']=self.legacySwitchOptions[w]['name']
        self.links[self.link]['options']=None
        self.links[self.link]['type']=None
        #self.liens.append(self.link)
        #self.DataLinkBindings()
        self.linkWidget=w
        self.source[w]=self.link

    def DataLinkBindings(self):

        def linkColorEntry(_event,link=self.link):
            self.selectedLink=link
            self.canvas.itemconfig(link,fill='red')

        def linkColorLeave(_event,link=self.link):
            self.canvas.itemconfig(link,fill='blue')

        self.canvas.tag_bind(self.link,'<Enter>',linkColorEntry)
        self.canvas.tag_bind(self.link,'<Leave>',linkColorLeave)
        self.canvas.tag_bind(self.link,'<Button-3>',self.popup_link)


    def dragLink(self,event):
        b = self.canvasx( event.x_root ) # coordonnées d'arrivée
        n = self.canvasy( event.y_root ) # coordonnées d'arrivée
        self.canvas.coords(self.link,self.coordonnees["i0"],self.coordonnees["j0"],b,n)

    def ControlLinkBindings( self ):

        def linkColorEntry1(_event,link=self.link ):
            self.selectedLink=link
            self.canvas.itemconfig(link,fill='blue')

        def linkColorLeave1( _event,link=self.link):
            self.canvas.itemconfig( link, fill='red' )

        self.canvas.tag_bind(self.link,'<Enter>',linkColorEntry1)
        self.canvas.tag_bind(self.link,'<Leave>',linkColorLeave1)

    def linkUp(self):
        link = self.selectedLink
        src = self.links[link]['src']
        #print('src '+str(src))
        dst = self.links[link]['dest']
        #print('dst ' + str(dst))
        self.net.configLinkStatus(src,dst,'up')
        self.canvas.itemconfig(link, dash=())

    def linkDown(self):
        link = self.selectedLink
        src = self.links[link]['src']
        dst = self.links[link]['dest']
        self.net.configLinkStatus(src,dst,'down')
        self.canvas.itemconfig(link, dash=())

    def finishLink(self,event):
        #we drag from the widget , we use root coordonnees
        src = self.linkWidget
        srcItem=self.widgetToItem[src]
        x = self.canvasx(event.x_root) # coordonnées d'arrivée du lien
        y= self.canvasy(event.y_root) # coordonnées d'arrivée du lien
        target = self.findObject(x,y) # item du widget d'arrivée
        srctags=self.canvas.gettags(srcItem)
        desttags=self.canvas.gettags(target)
        dest1=self.itemToWidget.get(target,None) #widget correspondant à l'item se trouvant à l'arrivée

        if(dest1 == None):
            self.canvas.delete( self.link )
            del self.source[src]
            del self.links[self.link]
            return
            #self.link=None
            #self.linkWidget=None

        if (dest1 != None):
            tags=self.canvas.gettags(target)
            if('Switch' in tags):
                self.links[self.link]['dest']=self.switchOptions[dest1]['nameSwitch']
            elif('host' in tags):
                self.links[self.link]['dest']=self.hostOptions[dest1]['hostname']
            elif('Controller' in tags):
                self.links[self.link]['dest']=self.controllerOptions[dest1]['hostname']
            elif('LegacySwitch' in tags):
                self.links[self.link]['dest']=self.legacySwitchOptions[dest1]['name']
            elif('LegacyRouter' in tags):
                self.links[self.link]['dest']=self.legacyRouterOptions[dest1]['name']

        if(('host' in srctags and 'host' in desttags) or
              ('Controller' in srctags and 'LegacyRouter' in desttags)or
              ('LegacyRouter' in srctags and 'Controller' in desttags)or
              ('Controller' in srctags and 'LegacySwitch' in desttags)or
              ('LegacySwitch' in srctags and 'Controller' in desttags)or
              ('Controller' in srctags and 'host' in desttags)or
              ('host' in srctags and 'Controller' in desttags)or
              ('Controller' in srctags and 'Controller' in desttags)):
              self.canvas.delete(self.link)
              del self.links[self.link]
              return
              #self.link=None
              #self.linkWidget=None
        elif(('Controller' in srctags and 'Switch' in desttags)or
            ('Switch' in srctags and 'Controller' in desttags)):
            linkType='control'
            self.links[self.link]['type']='control'
            self.canvas.itemconfig(self.link,dash=(6, 4, 2, 4),fill='red')
            self.ControlLinkBindings()
            self.canvas.itemconfig(self.link,tags=self.canvas.gettags(self.link)+(linkType,))
            self.liens.append(self.link)
        else:
            #print("i m not a controller , setting links")
            linkType='data'
            self.links[self.link]['type']='data'
            self.DataLinkBindings()
            self.canvas.itemconfig(self.link,tags=self.canvas.gettags(self.link)+(linkType,))
            self.liens.append(self.link)

        if(('Controller' in srctags and 'Switch' in desttags)):
            controller_item=self.widgetToItem[src]
            controllerName=self.itemToName[controller_item]
            switch_name=self.itemToName[target]
            switch_options=self.switchOptions[dest1]['options']
            switch_options['controllers'].append(controllerName)

        if(('Switch' in srctags and 'Controller' in desttags)):
            switch_item=self.widgetToItem[src]
            switchname=self.itemToName[switch_item]
            controller_name=self.itemToName[target]
            switchoptions=self.switchOptions[src]['options']
            switchoptions['controllers'].append(controller_name)
            print('finishlink')
            print(self.switchOptions)
            print('\n')
        self.link=None
        self.linkWidget=None


    def dumpNodes(self,nodes):
        root=Toplevel()
        root.title('Net')
        text1=Text(root,height=10,width=60)
        scroll = Scrollbar(root, command=text1.yview)
        #scroll1=Scrollbar(root,command=text1.xview)
        text1.configure(yscrollcommand=scroll.set)
        #text1.configure(xscrollcommand=scroll1.set)
        text1.tag_configure('big',justify='center',font=('Helvetica',16,'bold'),foreground='RoyalBlue1',underline=1)
        text1.tag_configure('color',font=('Helvetica',11,'bold'))
        text1.config(state="normal")
        text1.insert(END,'\nLinks between nodes\n\n','big')
        for node in nodes:
            text1.insert(INSERT,str(node.name)+' ','color')
            for intf in node.intfList():
                text1.insert(INSERT,str(intf)+':','color')
                if intf.link:
                    intfs = [ intf.link.intf1, intf.link.intf2 ]
                    intfs.remove( intf )
                    text1.insert(INSERT,intfs[0],'color')
                    text1.insert(INSERT,' ','color')
                else:
                    text1.insert(INSERT,' ','color')
            text1.insert(INSERT,'\n')
        text1.config(state='disabled')
        text1.pack(side=LEFT)
        scroll.pack(side=RIGHT,fill=Y)
        #scroll1.pack(side=BOTTOM,fill=X)

    def dumpNet(self):
        nodes=self.net.controllers + self.net.switches + self.net.hosts
        self.dumpNodes(nodes)

    def start( self ):
        setLogLevel('info')
        if self.net is None:
            self.net = self.build1()
            info( '**** Starting %s controllers\n' % len(self.net.controllers))
            for controller in self.net.controllers:
                info(str(controller) + ' ')
                controller.start()

            info('\n')
            info('**** Starting %s switches\n' % len(self.net.switches))

            for widget in self.widgetToItem:
                item=self.widgetToItem[widget]
                name=self.itemToName[item]
                tags = self.canvas.gettags(item)
                if 'Switch' in tags:
                    options = self.switchOptions[widget]
                    switch_options=options['options']
                    switchControllers = []
                    #print('def start')
                    #print(self.switchOptions)
                    #print('\n')
                    for ctrl in switch_options['controllers']:
                        switchControllers.append(self.net.get(ctrl))
                    info(name+ ' ')

                    self.net.get(name).start(switchControllers)

                if 'LegacySwitch' in tags:
                    self.net.get(name).start( [] )
                    info( name + ' ')

            info('\n')

            self.postStartSetup()

    def postStartSetup(self):
        setLogLevel('info')
        # Setup host details
        for widget in self.widgetToItem:
            item=self.widgetToItem[widget]
            name = self.itemToName[item]
            tags = self.canvas.gettags(item)

            if 'host' in tags:
                newHost = self.net.get(name)
                host_options= self.hostOptions[widget]['options']

                # Attach vlan interfaces
                if ('vlanInterfaces' in host_options and len(host_options['vlanInterfaces'])>0):
                    for vlanInterface in host_options['vlanInterfaces']:
                        info( 'adding vlan interface '+vlanInterface[1], '\n' )
                        newHost.cmdPrint('ifconfig '+name+'-eth0.'+vlanInterface[1]+' '+vlanInterface[0])

                # Run User Defined Start Command
                if ('startCommand' in host_options and len(host_options['startCommand'])>0):
                    newHost.cmdPrint(host_options['startCommand'])

            if 'Switch' in tags:
                newNode = self.net.get(name)
                switch_options = self.switchOptions[widget]['options']
                # Run User Defined Start Command
                if ('startCommand' in switch_options and len(switch_options['startCommand'])>0):
                    newNode.cmdPrint(switch_options['startCommand'])

        # Configure NetFlow
        nflowValues = self.preferences['netflow']
        if len(nflowValues['nflowTarget']) > 0:
            nflowEnabled = False
            nflowSwitches = ''
            for widget in self.widgetToItem:
                item1=self.widgetToItem[widget]
                name=self.itemToName[item1]
                tags = self.canvas.gettags(item1)

                if 'Switch' in tags:
                    switch_opts = self.switchOptions[widget]['options']
                    if ('netflow' in switch_opts):
                        if switch_opts['netflow'] == 1:
                            info( name + ' has Netflow enabled\n' )
                            nflowSwitches = nflowSwitches + ' -- set Bridge ' + name + ' netflow=@MiniEditNF'
                            nflowEnabled=True
            if nflowEnabled:
                nflowCmd = 'ovs-vsctl -- --id=@MiniEditNF create NetFlow '+ 'target=\\\"'+nflowValues['nflowTarget']+'\\\" '+ 'active-timeout='+nflowValues['nflowTimeout']
                if nflowValues['nflowAddId'] == 1:
                    nflowCmd = nflowCmd + ' add_id_to_interface=true'
                else:
                    nflowCmd = nflowCmd + ' add_id_to_interface=false'
                info('cmd =' + nflowCmd + nflowSwitches,'\n')
                call(nflowCmd+nflowSwitches, shell=True)

            else:
                info( 'No switches with Netflow\n' )
        else:
            info( 'No NetFlow targets specified.\n' )

        # Configure sFlow
        sflowValues = self.preferences['sflow']
        if len(sflowValues['sflowTarget']) > 0:
            sflowEnabled = False
            sflowSwitches = ''
            for widget in self.widgetToItem:
                item2=self.widgetToItem[widget]
                name2=self.itemToName[item2]
                tags = self.canvas.gettags(item2)

                if 'Switch' in tags:
                    switch_opts1 = self.switchOptions[widget]['options']
                    if ('sflow' in switch_opts1):
                        if switch_opts1['sflow'] == 1:
                            info( name+' has sflow enabled\n' )
                            sflowSwitches = sflowSwitches + '-- set Bridge' + name + 'sflow=@MiniEditSF'
                            sflowEnabled=True

            if sflowEnabled:
                sflowCmd = 'ovs-vsctl -- --id=@MiniEditSF create sFlow ' + 'target=\\\"' + sflowValues['sflowTarget'] + '\\\" ' + 'header=' + sflowValues['sflowHeader'] + ' ' + 'sampling=' + sflowValues['sflowSampling'] + ' ' + 'polling=' + sflowValues['sflowPolling']
                info( 'cmd = '+sflowCmd+sflowSwitches, '\n' )
                call( sflowCmd + sflowSwitches, shell=True)
            else:
                info( 'No switches with sflow\n')

        else:
            info( 'No sFlow targets specified.\n' )

        if str(self.preferences['startCLI']) == '1':
            info( "\n\n NOTE: PLEASE REMEMBER TO EXIT THE CLI BEFORE YOU PRESS THE STOP BUTTON. Not exiting will prevent MiniEdit from quitting and will prevent you from starting the network again during this sessoin.\n\n")
            CLI(self.net)

    def changehostname(self,*args):
        hostnames['host0']=var_name.get()
        host_nodes[0]=self.name_host[hostnames['host0']]
        #print("host_nodes"+str(host_nodes)+'\n')

    def changehostname1(self,*args):
        hostnames['host1']=var_name1.get()
        host_nodes[1]=self.name_host[hostnames['host1']]
        #print("host_nodes 1 " + str(host_nodes) + '\n')

    def pingpair(self):
        global host_nodes
        global hostnames
        hostnames={}
        global var_name
        global var_name1
        name_hosts=()
        for host in self.name_host.keys():
            name_hosts=name_hosts+(str(host),)
        #print(name_hosts)
        root=Toplevel()
        root.geometry('300x150')
        helv36 = Font(family='Helvetica', size=10, weight='bold')
        label=Label(root,text='Available nodes',font=helv36)
        label.place(x=100,y=0)

        label1=Label(root,text='Choose nodes',font=helv36)
        label1.place(x=110,y=30)
        hostnames['host0']=name_hosts[0]
        hostnames['host1']=name_hosts[0]
        host_nodes=[self.name_host[hostnames['host0']],self.name_host[hostnames['host1']]]
        var_name=StringVar()
        var_name.trace("w",self.changehostname)
        var_name1=StringVar()
        var_name1.trace("w",self.changehostname1)
        var_name.set(name_hosts[0])
        var_name1.set(name_hosts[0])
        dropDownMenu=OptionMenu(root,var_name,*name_hosts)
        dropDownMenu.place(x=85,y=60)
        dropDownMenu1=OptionMenu(root,var_name1,*name_hosts)
        dropDownMenu1.place(x=175,y=60)
        #hosts_nodes=[self.name_host[hostnames['host0']],self.name_host[hostnames['host1']]]
        #cmd = lambda arg1=hosts_nodes : self.pinghosts(arg1,timeout=None)
        bouton = Button(root,text='OK',command=partial(self.pinghosts1,host_nodes))
        bouton.place(x=135,y=100)

    def stop_net( self ):
        if self.net is not None:
            for widget in self.widgetToItem:
                item=self.widgetToItem[widget]
                name = self.itemToName[item]
                tags = self.canvas.gettags(item)
                if 'host' in tags:
                    newHost = self.net.get(name)
                    host_options = self.hostOptions[widget]['options']
                    if ('stopCommand' in host_options and len(host_options['stopCommand'])>0):
                        newHost.cmdPrint(self.hostOptions['stopCommand'])
                if 'Switch' in tags:
                    newNode = self.net.get(name)
                    switch_options = self.switchOptions[widget]['options']
                    if 'stopCommand' in switch_options:
                        newNode.cmdPrint(switch_options['stopCommand'])
            self.net.stop()

        cleanUpScreens()
        self.net = None

    def stop(self):
        setLogLevel('info')
        self.stop_net()
        for bouton in self.list_buttons.values():
            bouton.config(state='normal')

    def build1(self):
        setLogLevel('info')
        dpctl = None
        if len(self.preferences['dpctl'])!=0:
            dpctl = int(self.preferences['dpctl'])
        net = Mininet(topo=None,listenPort=dpctl,build=False,ipBase=self.preferences['ipBase'] )

        self.buildNodes(net)
        self.buildLinks(net)
        info('\n')
        net.build()
        return net

    def checkIntf(intf):
        if (' %s:' % intf) not in quietRun('ip link show'):
            showerror(title="Error",message='External interface ' + intf + ' does not exist! Skipping.')
            return False
        ips = re.findall( r'\d+\.\d+\.\d+\.\d+', quietRun( 'ifconfig ' + intf ) )
        if ips:
            showerror(title="Error",message= intf + ' has an IP address and is probably in use! Skipping.' )
            return False
        return True

    def buildNodes(self,net):
        setLogLevel( 'info' )
        info("Getting Hosts and Switches.\n")
        for item in self.widgetToItem.values():
            tags = self.canvas.gettags(item)
            name=str(self.itemToName[item])

            if 'Switch' in tags:
                options = self.switchOptions[self.itemToWidget[item]]
                switch_options=options['options']
                # Create switch class
                switchClass = customOvs
                switch_properties={}

                if ('dpctl' in switch_options and len(switch_options['dpctl'])>0):
                    switch_properties['listenPort']=int(switch_options['dpctl'])

                if ('dpid' in switch_options and len(switch_options['dpid'])>0):
                    switch_properties['dpid']=switch_options['dpid']

                if switch_options['switchType'] == 'Default':
                    if self.preferences['switchType'] == 'Indigo Virtual Switch':
                        switchClass = IVSSwitch
                    elif self.preferences['switchType'] == 'Userspace Switch':
                        switchClass = CustomUserSwitch
                    elif self.preferences['switchType'] == 'Userspace Switch inNamespace':
                        #print("Userspace switchhhh in namespaceee self preferences\n")
                        switch_properties['inNamespace'] = True
                        switchClass = CustomUserSwitch
                    else:
                        switchClass = customOvs

                elif switch_options['switchType'] == 'Userspace Switch':
                    switchClass = CustomUserSwitch

                elif switch_options['switchType'] == 'Userspace Switch inNamespace':
                    switchClass = CustomUserSwitch
                    switch_properties['inNamespace'] = True

                elif switch_options['switchType'] == 'Indigo Virtual Switch':
                    switchClass = IVSSwitch

                else:
                    #print("switch type:" + switch_options['switchType'])
                    #print('\n')
                    #print('It s custom OVS\n')
                    switchClass = customOvs

                if switchClass == customOvs:
                    # Set OpenFlow versions
                    self.openFlowVersions = []
                    if self.preferences['openFlowVersions']['ovsOf10'] == 1:
                        self.openFlowVersions.append('OpenFlow10')
                    if self.preferences['openFlowVersions']['ovsOf11'] == 1:
                        self.openFlowVersions.append('OpenFlow11')
                    if self.preferences['openFlowVersions']['ovsOf12'] == 1:
                        self.openFlowVersions.append('OpenFlow12')
                    if self.preferences['openFlowVersions']['ovsOf13'] == 1:
                        self.openFlowVersions.append('OpenFlow13')
                    protocolList = ",".join(self.openFlowVersions)
                    switch_properties['protocols'] = protocolList
                newSwitch = net.addSwitch(name,cls=switchClass,**switch_properties)
                self.nameswitch[name]=newSwitch

                #Setting IP address
                if switchClass == CustomUserSwitch:
                    if ('switchIP' in switch_options and len(switch_options['switchIP'])>0):
                        newSwitch.setSwitchIP(switch_options['switchIP'])
                if switchClass == customOvs:
                    if ('switchIP' in switch_options and len(switch_options['switchIP'])>0):
                        newSwitch.setSwitchIP(switch_options['switchIP'])

                # Attach external interfaces
                if ('externalInterfaces' in switch_options and len(switch_options['externalInterfaces'])>0):
                    for extInterface in switch_options['externalInterfaces']:
                        if self.checkIntf(extInterface):
                            Intf(extInterface,node=newSwitch)

            elif 'LegacySwitch' in tags:
                newSwitch = net.addSwitch(name,cls=LegacySwitch)
                self.nameswitch[name]=newSwitch

            elif 'LegacyRouter' in tags:
                newhost = net.addHost(name,cls=LegacyRouter)
                self.name_host[name]=newhost
                self.hosts.append(newhost)

            elif 'host' in tags:
                options = self.hostOptions[self.itemToWidget[item]]
                host_options=options['options']

                ip = None
                defaultRoute = None
                if('defaultRoute' in host_options and len(host_options['defaultRoute'])>0):
                    defaultRoute='via' + host_options['defaultRoute']
                if ('ip' in host_options and len(host_options['ip'])>0):
                    ip = host_options['ip']
                else:
                    nodeNum = self.hostOptions[self.itemToWidget[item]]['numhost']
                    ipBaseNum, prefixLen=netParse(self.preferences['ipBase'])
                    ip=ipAdd(i=nodeNum, prefixLen=prefixLen, ipBaseNum=ipBaseNum)

                # Create correct host class
                if ('cores' in host_options and len(host_options['cores'])>0) or ('cpu' in host_options and len(host_options['cpu'])>0):
                    if ('privateDirectory' in host_options and len(host_options['privateDirectory'])>0):
                        hostCls=partial(CPULimitedHost,privateDirs=host_options['privateDirectory'] )
                    else:
                        hostCls=CPULimitedHost
                else:
                    if ('privateDirectory' in host_options and len(host_options['privateDirectory'])>0) :
                        hostCls=partial(Host,privateDirs=host_options['privateDirectory'])
                    else:
                        hostCls=Host

                debug(hostCls,'\n')

                hostnew = net.addHost(name,cls=hostCls,ip=ip,defaultRoute=defaultRoute)
                # print('hostnew\n')
                # print(hostnew)
                # print('name'+name+'\n')
                # print('cls host\n')
                # print(hostCls)
                # print('iphost:'+ip+'\n')
                # print('defaultroute')
                # print(defaultRoute)

                self.hosts.append(hostnew)
                self.name_host[name]=hostnew

                # Set the CPULimitedHost specific options
                if ('cores' in host_options and len(host_options['cores'])>0):
                    newHost.setCPUs(cores = host_options['cores'])
                    #print('cooores host\n')
                if ('cpu' in host_options and len(host_options['cpu'])>0):
                    newHost.setCPUFrac(f=host_options['cpu'], sched=host_options['sched'])
                    #print('cpuuu host\n')

                # Attach external interfaces
                if ('externalInterfaces' in host_options and len(host_options['externalInterfaces'])>0):
                    #print("external Interface host")
                    for extInterface in host_options['externalInterfaces']:
                        if self.checkIntf(extInterface):
                            #print("external Interface host")
                            Intf(extInterface,node=newHost)

                if ('vlanInterfaces' in host_options and len(host_options['vlanInterfaces'])>0):
                        info( 'Checking that OS is VLAN prepared\n' )
                        self.pathCheck('vconfig', moduleName='vlan package')
                        moduleDeps( add='8021q' )

            #Make controller
            elif 'Controller' in tags:
                options = self.controllerOptions[self.itemToWidget[item]]
                controller_options = options['options']
                # print('controller_options')
                # print(controller_options)
                # print('\n')

                controllerType = controller_options['controllerType']
                if ('controllerProtocol' in controller_options and len(controller_options['controllerProtocol'])>0):
                    controllerProtocol = controller_options['controllerProtocol']
                    # print('controllerProtocol'+controllerProtocol)
                    # print('\n')
                else :
                    controllerProtocol = 'tcp'
                    controller_options['controllerProtocol'] = 'tcp'

                controllerIP = str(controller_options['remoteIP'])
                controllerPort = int(controller_options['remotePort'])
                #print("controllerPort :" + str(controllerPort))

                info('Getting controller selection:' + str(controllerType)+'\n')
                if controllerType == 'Remote Controller':
                    control1=net.addController(name=name,controller=RemoteController,ip=controllerIP,protocol=controllerProtocol,port=int(controllerPort))
                    self.namecontroller[name]=control1
                elif controllerType == 'In-Band Controller':
                    control2=net.addController(name=name,controller=InbandController,ip=controllerIP,protocol=controllerProtocol,port=int(controllerPort))
                    self.namecontroller[name]=control2
                elif controllerType == 'OVS Controller':
                    control3=net.addController(name=name,controller=OVSController,protocol=controllerProtocol,port=int(controllerPort))
                    self.namecontroller[name]=control3
                else:
                    control4=net.addController(name=name,controller=Controller,protocol=controllerProtocol,port=int(controllerPort))
                    # print('namecontrol'+name)
                    # print(Controller)
                    # print('\n')
                    # print('controllerProtocol'+controllerProtocol)
                    # print('controllerPort'+str(controllerPort))
                    # print('\n')
                    # print(control4)

                    self.namecontroller[name]=control4
            else:
                raise Exception( "Cannot create mystery node: " + name )

    def buildLinks(self,net):
        # Make links
        setLogLevel('info')
        info( "Getting Links.\n" )
        for link in self.links.keys():
            tags = self.canvas.gettags(link)
            if 'data' in tags:
                #print('we are in data link\n')
                src=self.links[link]['src']
                #print('src'+src+'\n')
                dst=self.links[link]['dest']
                #print('dst'+dst+'\n')
                linkopts=self.links[link]['options']
                #print('linkopts')
                #print(linkopts)
                if linkopts:
                    #print(linkopts)
                    #print('linkopts')
                    net.addLink(src,dst,cls=TCLink, **linkopts)
                else:
                    #print('linkoptions are none\n')
                    net.addLink(src,dst)

    def netImages(self):
        img1=PhotoImage(file="/home/user/Desktop/graph/switch.gif")
        img2=PhotoImage(file="/home/user/Desktop/graph/controleur.png")
        img3=PhotoImage(file="/home/user/Desktop/graph/host.png")
        img4=PhotoImage(file="/home/user/Desktop/graph/line.png")
        img5=PhotoImage(file="/home/user/Desktop/graph/legacyRouter.png")
        img6=PhotoImage(file="/home/user/Desktop/graph/legacyswitch.png")
        img1_mini=img1.subsample(15,15)
        img2_mini=img2.subsample(7,7)
        img3_mini=img3.subsample(8,8)
        img4_mini=img4.subsample(7,7)
        img5_mini=img5.subsample(16,16)
        img6_mini=img6.subsample(6,6)
        dict_images={'Switch': img1_mini,'Controller':img2_mini,'Host':img3_mini,'Link':img4_mini,'LegacyRouter':img5_mini,'LegacySwitch':img6_mini}
        return dict_images


def main():
    fenetre= Tk()
    fenetre.title('New Miniedit')
    fenetre['bg']="white"
    fenetre.geometry("1000x1000")

    interface = Interface(fenetre)
    fenetre.mainloop()

if __name__ == '__main__':
    main()
