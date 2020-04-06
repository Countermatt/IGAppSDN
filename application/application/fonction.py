#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import *
from PIL import Image,ImageTk
#from Tkinter import ttk
from tkinter import ttk
from tkinter import filedialog
import logging
from mininet.net import Mininet, VERSION
#from Tkinter import filedialog as tkFileDialog
from mininet.util import netParse,ipAdd
from time import sleep
from mininet.link import TCLink, Intf, Link
from mininet.log import info
from mininet.log import debug
from mininet.log import warn,setLogLevel
from mininet.net import Mininet, VERSION
from mininet.util import netParse, ipAdd, quietRun
from mininet.util import buildTopo
from mininet.util import custom, customClass
from mininet.term import makeTerm, cleanUpScreens
from mininet.node import Controller, RemoteController, NOX, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSSwitch, UserSwitch
from mininet.link import TCLink, Intf, Link
from distutils.version import StrictVersion
from mininet.cli import CLI
from mininet.moduledeps import moduleDeps
from mininet.topo import SingleSwitchTopo, LinearTopo, SingleSwitchReversedTopo
from mininet.topolib import TreeTopo
from mininet.node import IVSSwitch
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
