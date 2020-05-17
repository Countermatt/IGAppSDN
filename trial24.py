#!/usr/bin/python
# -*- coding: utf-8 -*-

from Tkinter import *
from PIL import Image,ImageTk
#from Tkinter import ttk
import ttk
import time
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

class switchWindow(object):

    def __init__(self, master,name):
        self.top=Toplevel(master)
        self.top.geometry('500x500')
        self.nameswitch = StringVar()
        self.nameswitch.set(name)
        self.content = StringVar()
        self.infoswitch = {}
        self.listboxInt = None
        self.listInt = []
        self.valueNetFlow = IntVar()
        self.value_sFlow = IntVar()
        self.switchType = StringVar()
        self.result=None
        self.switchProperties(self.top)

    def switchProperties(self,window):
        Options=["Default","Open VSwitch Kernel Mode","Indigo Virtual Switch","Userspace Switch","Userspace Switch inNamespace"]

        #Switch Name
        label_hostname=Label(self.top,text="Hostname :",width=20,font=("bold",10))
        label_hostname.place(x=0,y=10)
        entry_hostname=Entry(self.top,textvariable=self.nameswitch)
        entry_hostname.place(x=130,y=10)
        self.infoswitch['nameSwitch'] = entry_hostname

        #External Interfaces
        labelInt=Label(self.top,text="External Interface :",width=20,font=("bold",10))
        labelInt.place(x=290,y=10)
        bouton_add=Button(self.top,text="Add",command=self.addListbox)
        bouton_add.place(x=440,y=8)

        labelExt=Label(self.top,text="External Interfaces")
        labelExt.place(x=330,y=50)
        frame=Frame(self.top, width=170, height=320)
        frame.place(x=320,y=80)
        entryInt=Entry(frame,textvariable=self.content)
        entryInt.pack()
        scroll= Scrollbar(frame)
        scroll.pack(side=RIGHT,fill=Y)
        self.listboxInt=Listbox(frame,yscrollcommand=scroll.set)
        self.listboxInt.pack()
        scroll.config(command=self.listboxInt.yview)

        #DPID
        label_dpid=Label(self.top,text="DPID :",width=20,font=("bold",10))
        label_dpid.place(x=0,y=40)
        entry_dpid=Entry(self.top)
        entry_dpid.place(x=110,y=40)
        self.infoswitch["dpid"]=entry_dpid

        #EnableNetFlow
        labelNetFlow=Label(self.top,text="Enable NetFlow :",width=20,font=("bold",10))
        labelNetFlow.place(x=0,y=70)
        boutonNetFlow=Checkbutton(self.top,variable=self.valueNetFlow)
        boutonNetFlow.place(x=130,y=70)

        #EnablesFlow
        label_sflow = Label(self.top,text="Enable sFlow :",width=20,font=("bold",10))
        label_sflow.place(x=0,y=100)
        bouton_sFlow = Checkbutton(self.top,variable=self.value_sFlow)
        bouton_sFlow.place(x=130,y=100)

        #Switch Type
        label_type=Label(self.top,text="Switch Type",width=20,font=("bold",10))
        label_type.place(x=0,y=130)
        self.switchType.set(Options[0])
        self.switchType.trace("w",self.changeswitchType)
        dropDownMenu=OptionMenu(self.top,self.switchType,Options[0],Options[1],Options[2],Options[3],Options[4])
        dropDownMenu.place(x=130,y=130)

        #IP address
        label_ip=Label(self.top,text="IP Address :",width=20,font=("bold",10))
        label_ip.place(x=0,y=160)
        entry_ip=Entry(self.top)
        entry_ip.place(x=130,y=160)
        self.infoswitch["ipAddress"]=entry_ip

        label_port=Label(self.top,text="DPCTL port :",width=20,font=("bold",10))
        label_port.place(x=0,y=190)
        entry_port=Entry(self.top)
        entry_port.place(x=130,y=190)
        self.infoswitch['dpctlPort']=entry_port

        labelstartCommand=Label(self.top,text="Start Command :",width=20,font=("bold",10))
        labelstartCommand.place(x=0,y=320)
        entrystartCommand=Entry(self.top)
        entrystartCommand.place(x=140,y=320,width=350)
        self.infoswitch['start']=entrystartCommand

        labelstopCommand=Label(self.top,text="Stop Command :",width=20,font=("bold",10))
        labelstopCommand.place(x=0,y=350)
        entrystopCommand=Entry(self.top)
        entrystopCommand.place(x=140,y=350,width=350)
        self.infoswitch['stop']=entrystopCommand

        bouton_ok=Button(self.top,text='OK',width=10,command=self.okAction)
        bouton_ok.place(x=200,y=420)
        bouton_cancel=Button(self.top,text='Cancel',width=10,command=lambda : sel.top.destroy())
        bouton_cancel.place(x=350,y=420)

    def setResult(self):
        setLogLevel('info')
        self.result={}
        self.result['hostname']=self.infoswitch['nameSwitch'].get()
        self.result['switchIP']=self.infoswitch['ipAddress'].get()
        self.result['dpctl']=self.infoswitch['dpctlPort'].get()
        self.result['dpid']=self.infoswitch['dpid'].get()
        self.result['switchType']=self.switchType.get()
        self.result['sflow']= self.value_sFlow.get()
        self.result['netflow']=self.valueNetFlow.get()
        self.result['externalInterfaces']= self.listInt
        self.result['startCommand']=self.infoswitch['start'].get()
        self.result['stopCommand']=self.infoswitch['stop'].get()

    def addListbox(self):
        self.listboxInt.insert(END,self.content.get())
        self.listInt.append(self.content.get())

    def changeswitchType(self,*args):
        self.infoswitch['switchType']=self.switchType.get()

    def okAction(self):
        self.setResult()
        self.top.destroy()

class hostWindow(object):

    def __init__(self, master,name):
        self.top=Toplevel(master)
        self.top.geometry('500x500')
        self.namehost = StringVar()
        self.namehost.set(name)
        self.varCPU=StringVar()
        self.result = None
        self.contentVLANaddress=StringVar()
        self.contentVLANid=StringVar()
        self.contentExternal=StringVar()
        self.content_directory=StringVar()
        self.content_dir = StringVar()
        self.listbox_directory=None
        self.listbox_dir=None
        self.directoryEntries=[]
        self.listboxVLANaddress=None
        self.listboxVLANid=None
        self.listboxInt = None
        self.hostEntries={}
        self.vlanEntries=[]
        self.externalEntries=[]
        self.hostProperties(self.top)

    def hostProperties(self,window):
            options=['host','cfs','rt']

            notebook = ttk.Notebook(window)
            self.frameProperties=ttk.Frame(notebook)
            self.frameVLAN=ttk.Frame(notebook)
            self.frameInt=ttk.Frame(notebook)
            self.framedirectory=ttk.Frame(notebook)
            notebook.add(self.frameProperties,text="Properties")
            notebook.add(self.frameVLAN,text="VLAN Interfaces")
            notebook.add(self.frameInt,text="External Interfaces")
            notebook.add(self.framedirectory,text="Private Directories")
            notebook.pack(fill="both",expand="yes")

            #hostname
            label_hostname=Label(self.frameProperties,text="Hostname :",width=20,font=("bold",10))
            label_hostname.place(x=1,y=20)
            entry_hostname = Entry(self.frameProperties,textvariable=self.namehost)
            entry_hostname.place(x=150,y=20)
            self.hostEntries['hostname'] = entry_hostname

            #ipAddress
            label_ip=Label(self.frameProperties,text="IP Address :",width=20,font=("bold",10))
            label_ip.place(x=1,y=50)
            entry_ip=Entry(self.frameProperties)
            entry_ip.place(x=150,y=50)
            self.hostEntries['ipAddress']=entry_ip

            #DefaultRoute
            label_defaultRoute=Label(self.frameProperties,text="Default Route :",width=20,font=("bold",10))
            label_defaultRoute.place(x=1,y=80)
            entry_defaultRoute=Entry(self.frameProperties)
            entry_defaultRoute.place(x=150,y=80)
            self.hostEntries['defaultRoute']=entry_defaultRoute

            #CPU
            label_cpu=Label(self.frameProperties,text="Amount CPU :",width=20,font=("bold",10))
            label_cpu.place(x=1,y=110)
            entry_cpu=Entry(self.frameProperties)
            entry_cpu.place(x=150,y=110)
            self.hostEntries['cpu']=entry_cpu

            self.hostEntries['sched']=options[0]
            self.varCPU.set(options[0])
            self.varCPU.trace("w",self.changeCPU)
            dropDownMenu=OptionMenu(self.frameProperties,self.varCPU,options[0],options[1],options[2])
            dropDownMenu.place(x=350,y=110)

            #Cores
            label_cores=Label(self.frameProperties,text="Cores :",width=20,font=("bold",10))
            label_cores.place(x=1,y=140)
            entry_cores=Entry(self.frameProperties)
            entry_cores.place(x=150,y=140)
            self.hostEntries['cores']=entry_cores

            # #Start Command
            label_startCommand=Label(self.frameProperties,text="Start Command :",width=20,font=("bold",10))
            label_startCommand.place(x=1,y=170)
            entry_startCommand=Entry(self.frameProperties)
            entry_startCommand.place(x=150,y=170)
            self.hostEntries['start']=entry_startCommand

            # #Stop Command
            label_stopCommand=Label(self.frameProperties,text="Stop Command :",width=20,font=("bold",10))
            label_stopCommand.place(x=1,y=200)
            entry_stopCommand=Entry(self.frameProperties)
            entry_stopCommand.place(x=150,y=200)
            self.hostEntries['stop']=entry_stopCommand

            boutonProperties=Button(self.frameProperties,text="OK",width=8,height=2,command=self.okAction)
            boutonProperties.place(x=1,y=400)

            boutonCancel = Button(self.frameProperties,text="Cancel",width=8,height=2,command=lambda : self.top.destroy())
            boutonCancel.place(x=100,y=400)

            # #Frame 2 VLAN INTERFACE
            label_VLANInt=Label(self.frameVLAN,text="VLAN Interface:",width=20,font=("bold",10))
            label_VLANInt.place(x=50,y=10)
            boutonaddVLAN=Button(self.frameVLAN,text='Add',command= self.addVLANInterface,width=5,height=1)
            boutonaddVLAN.place(x=200,y=10)

            frame=Frame(self.frameVLAN,highlightbackground="black", highlightcolor="black",highlightthickness=1,width=400,height=300,bd=0)
            frame.place(x=50,y=50)
            sousFrame = Frame(frame, highlightbackground="black", highlightcolor="black", highlightthickness=1, width=200, height=20, bd= 0)
            sousFrame.place(x=20,y=10)

            label_ipAddress=Label(sousFrame,text="IP Address",width=20)
            label_ipAddress.pack()
            entry_ipAddress=Entry(sousFrame,textvariable=self.contentVLANaddress)
            entry_ipAddress.pack()

            frameVLANid = Frame(frame, highlightbackground="black", highlightcolor="black", highlightthickness=1, width=200, height=20, bd= 0)
            frameVLANid.place(x=180,y=10)
            label_VLANid=Label(frameVLANid,text="VLAN ID",width=20)
            label_VLANid.pack()
            entry_VLANid=Entry(frameVLANid,textvariable=self.contentVLANid)
            entry_VLANid.pack()

            scroll= Scrollbar(sousFrame)
            scroll.pack(side=RIGHT,fill=Y)
            self.listboxVLANaddress = Listbox(sousFrame,yscrollcommand=scroll.set)
            self.listboxVLANaddress.pack()
            scroll.config(command=self.listboxVLANaddress.yview)

            scroll = Scrollbar(frameVLANid)
            scroll.pack(side=RIGHT,fill=Y)
            self.listboxVLANid=Listbox(frameVLANid,yscrollcommand=scroll.set)
            self.listboxVLANid.pack()
            scroll.config(command=self.listboxVLANid.yview)

            # #Frame5  External Interfaces

            labelExt=Label(self.frameInt,text="External Interface :")
            labelExt.place(x=1,y=10)
            bouton_add=Button(self.frameInt,text='Add',command=self.addExternalInterface)
            bouton_add.place(x=130,y=5)
            frameBlack=Frame(self.frameInt,highlightbackground="black", highlightcolor="black",highlightthickness=1,width=250,height=300,bd=0)
            frameBlack.place(x=1,y=50)
            sousFrameBlack=Frame(frameBlack,highlightbackground="black", highlightcolor="black",highlightthickness=1,width=200,height=20,bd=0)
            sousFrameBlack.place(x=1,y=10)
            labelName=Label(sousFrameBlack,text="Interface Name")
            labelName.pack()
            entryExternal=Entry(sousFrameBlack,textvariable=self.contentExternal)
            entryExternal.pack()
            sousFrameBlack1=Frame(frameBlack,highlightbackground="black", highlightcolor="black",highlightthickness=1,width=200,height=300,bd=0)
            sousFrameBlack1.place(x=1,y=80)

            scroll= Scrollbar(sousFrameBlack1)
            scroll.pack(side=RIGHT,fill=Y)
            self.listboxInt=Listbox(sousFrameBlack1,yscrollcommand=scroll.set)
            self.listboxInt.pack()
            scroll.config(command=self.listboxInt.yview)

            # bouton11=Button(frame2,text="OK",width=10,height=2)
            # bouton11.place(x=150,y=380)
            # bouton12=Button(frame2,text="Cancel",command=lambda:fen.destroy(),width=10,height=2)
            # bouton12.place(x=260,y=380)

            # bouton13=Button(frame5,text="OK",width=10,height=2)
            # bouton13.place(x=10,y=380)
            # bouton14=Button(frame5,text="Cancel",command=lambda:fen.destroy(),width=10,height=2)
            # bouton14.place(x=120,y=380)
            #
            # bouton15=Button(frame6,text="OK",width=10,height=2)
            # bouton15.place(x=150,y=380)
            # bouton16=Button(frame6,text="Cancel",command=lambda:fen.destroy(),width=10,height=2)
            # bouton16.place(x=260,y=380)

            # #frame 6 PRIVATE DIRECTORIES
            label_directory=Label(self.framedirectory,text="Private Directory:",width=20,font=("bold",10))
            label_directory.place(x=50,y=10)
            bouton_add=Button(self.framedirectory,text='Add',command= self.addDirectory,width=5,height=1)
            bouton_add.place(x=200,y=10)

            framedir=Frame(self.framedirectory,highlightbackground="black", highlightcolor="black",highlightthickness=1,width=400,height=300,bd=0)
            framedir.place(x=50,y=50)
            sousFramedir=Frame(framedir, highlightbackground="black", highlightcolor="black", highlightthickness=1, width=200, height=20, bd= 0)
            sousFramedir.place(x=20,y=10)

            label_mount=Label(sousFramedir,text="Mount",width=20)
            label_mount.pack()
            entry_directory=Entry(sousFramedir,textvariable=self.content_directory)
            entry_directory.pack()

            sousFramedir1 = Frame(framedir, highlightbackground="black", highlightcolor="black", highlightthickness=1, width=200, height=20, bd= 0)
            sousFramedir1.place(x=180,y=10)
            label_persistent_directory=Label(sousFramedir1,text="Persistent Directory",width=20)
            label_persistent_directory.pack()
            entry_dir=Entry(sousFramedir1,textvariable=self.content_dir)
            entry_dir.pack()

            scroll= Scrollbar(sousFramedir)
            scroll.pack(side=RIGHT,fill=Y)
            self.listbox_directory=Listbox(sousFramedir,yscrollcommand=scroll.set)
            self.listbox_directory.pack()
            scroll.config(command=self.listbox_directory.yview)

            scroll= Scrollbar(sousFramedir1)
            scroll.pack(side=RIGHT,fill=Y)
            self.listbox_dir=Listbox(sousFramedir1,yscrollcommand=scroll.set)
            self.listbox_dir.pack()
            scroll.config(command=self.listbox_dir.yview)

    def addVLANInterface(self):
        self.listboxVLANaddress.insert(END,self.contentVLANaddress.get())
        self.listboxVLANid.insert(END,self.contentVLANid.get())
        self.vlanEntries.append([self.contentVLANaddress.get(),self.contentVLANid.get()])

    def addExternalInterface(self):
        self.listboxInt.insert(END,self.contentExternal.get())
        self.externalEntries.append(self.contentExternal.get())

    def addDirectory(self):
        self.listbox_directory.insert(END,self.content_directory.get())
        self.listbox_dir.insert(END,self.content_dir.get())
        self.directoryEntries.append((self.content_directory.get(),self.content_dir.get()))

    def changeCPU(self,*args):
        self.hostEntries['sched']=self.varCPU.get()

    def setResult(self):
        self.result={}
        self.result['hostname']=self.hostEntries['hostname'].get()
        self.result['ip']=self.hostEntries['ipAddress'].get()
        self.result['defaultRoute']=self.hostEntries['defaultRoute'].get()
        self.result['cores']=self.hostEntries['cores'].get()
        self.result['startCommand']=self.hostEntries['start'].get()
        self.result['stopCommand']=self.hostEntries['stop'].get()
        self.result['sched']=self.hostEntries['sched']
        self.result['cpu']=self.hostEntries['cpu'].get()
        self.result['externalInterfaces']=self.externalEntries
        self.result['privateDirectory']=self.directoryEntries
        self.result['vlanInterfaces']=self.vlanEntries

    def okAction(self):
        self.setResult()
        self.top.destroy()

    def cancelAction(self):
        self.top.destroy()

class ctrlWindow(object):

    def __init__(self, master,name):
        self.top=Toplevel(master)
        self.top.geometry('300x320')
        self.namecontroller = StringVar()
        self.namecontroller.set(name)
        self.ctrlProp={}
        self.result=None
        self.ctrlPort = StringVar()
        self.ctrlPort.set('6633')
        self.ctrlType = StringVar()
        self.ctrlType.set('OpenFlow Reference')
        self.ctrlProtocol = StringVar()
        self.ctrlProtocol.set('tcp')
        self.ctrladdress=StringVar()
        self.ctrladdress.set('127.0.0.1')
        self.ctrlProperties(self.top)

    def ctrlProperties(self,window):
        Options=['OpenFlow Reference','Remote Controller','In-Band Controller','OVS Controller']
        optionsProtocol=['tcp','ssl']

        labelName=Label(self.top,text='Name:')
        labelName.place(x=1,y=10)
        entryName=Entry(self.top,textvariable=self.namecontroller)
        entryName.place(x=120,y=10)
        self.ctrlProp['hostname']=entryName

        labelPort=Label(self.top,text='Controller Port:')
        labelPort.place(x=1,y=40)
        entryPort=Entry(self.top,textvariable=self.ctrlPort)
        entryPort.place(x=120,y=40)
        self.ctrlProp['remotePort']=entryPort

        labelType=Label(self.top,text='Controller Type:')
        labelType.place(x=1,y=70)
        self.ctrlType.trace("w",self.changeCtrlType)
        dropDownMenu=OptionMenu(self.top,self.ctrlType,Options[0],Options[1],Options[2],Options[3])
        dropDownMenu.place(x=120,y=70)

        labelProtocol=Label(self.top,text='Protocol:')
        labelProtocol.place(x=1,y=100)
        self.ctrlProtocol.trace("w",self.changeProtocol)
        dropDownMenu1=OptionMenu(self.top,self.ctrlProtocol,optionsProtocol[0],optionsProtocol[1])
        dropDownMenu1.place(x=120,y=110)

        frame=LabelFrame(self.top,text="Remote/In-Band Controller",width=280,height=60)
        frame.place(x=10,y=150)
        label_ip=Label(frame,text="IP Address:")
        label_ip.place(x=1,y=10)
        entry_address=Entry(frame,textvariable=self.ctrladdress)
        entry_address.place(x=90,y=10)
        self.ctrlProp['remoteIP']=entry_address

        bouton_ok=Button(self.top,text='OK',width=5,height=1,command=self.okAction)
        bouton_ok.place(x=50,y=230)
        bouton_cancel=Button(self.top,text='Cancel',width=5,height=1,command=lambda:self.top.destroy())
        bouton_cancel.place(x=150,y=230)

    def changeCtrlType(self,*args):
        self.ctrlProp['controllerType']=self.ctrlType.get()

    def changeProtocol(self,*args):
        self.ctrlProp['controllerProtocol']=self.ctrlProtocol.get()

    def setResult(self):
        self.result={}
        self.result['hostname']=self.ctrlProp['hostname'].get()
        self.result['remotePort']=int(self.ctrlProp['remotePort'].get())
        self.result['remoteIP']=self.ctrlProp['remoteIP'].get()
        self.result['controllerType']=self.ctrlType.get()
        self.result['controllerProtocol']=self.ctrlProtocol.get()

    def okAction(self):
        self.setResult()
        self.top.destroy()


class linkWindow(object):

    def __init__(self, master):
        self.top=Toplevel(master)
        self.top.geometry("350x250")
        self.linkProp={}
        self.result=None
        self.linkProperties(self.top)

    def linkProperties(self,window):
        #Bandwidth
        labelBandwidth=Label(self.top,text='Bandwidth:',width=15,font=("bold",10))
        labelBandwidth.place(x=0,y=10)
        entryBandwidth=Entry(self.top)
        entryBandwidth.place(x=125,y=10)
        self.linkProp['bw']=entryBandwidth
        labelUnite=Label(self.top,text='Mbit')
        labelUnite.place(x=290,y=10)

        #Delay
        label_delay=Label(self.top,text='Delay:',width=15,font=("bold",10))
        label_delay.place(x=0,y=40)
        entry_delay=Entry(self.top)
        entry_delay.place(x=125,y=40)
        self.linkProp['delay']=entry_delay

        #Loss
        label_loss=Label(self.top,text='Loss:',width=15,font=("bold",10))
        label_loss.place(x=0,y=70)
        entry_loss=Entry(self.top)
        entry_loss.place(x=125,y=70)
        label_unite=Label(self.top,text='%')
        label_unite.place(x=290,y=70)
        self.linkProp['loss']=entry_loss

        #Max Queue Size
        label_queuesize=Label(self.top,text='Max Queue size:',width=15,font=("bold",10))
        label_queuesize.place(x=0,y=100)
        entry_queuesize=Entry(self.top)
        entry_queuesize.place(x=125,y=100)
        self.linkProp['max_queue_size']=entry_queuesize

        #Jitter
        labelJitter=Label(self.top,text='Jitter:',width=15,font=("bold",10))
        labelJitter.place(x=0,y=130)
        entryJitter=Entry(self.top)
        entryJitter.place(x=125,y=130)
        self.linkProp['jitter']=entryJitter

        #Speedup
        label_speedup=Label(self.top,text='Speedup:',width=15,font=("bold",10))
        label_speedup.place(x=0,y=160)
        entry_speedup=Entry(self.top)
        entry_speedup.place(x=125,y=160)
        self.linkProp['speedup']=entry_speedup

        bouton_ok=Button(self.top,text='OK',width=10,command=self.okAction)
        bouton_ok.place(x=80,y=200)
        bouton_cancel=Button(self.top,text='Cancel',width=10,command = lambda:self.top.destroy())
        bouton_cancel.place(x=210,y=200)

    def setResult(self):
        self.result = {}
        self.result['bw']=int(self.linkProp['bw'].get())
        self.result['delay']=self.linkProp['delay'].get()
        self.result['loss']=int(self.linkProp['loss'].get())
        self.result['max_queue_size']=int(self.linkProp['max_queue_size'].get())
        self.result['jitter']=self.linkProp['jitter'].get()
        self.result['speedup']=int(self.linkProp['speedup'].get())

    def okAction(self):
        self.setResult()
        self.top.destroy()

class prefWindow(object):

    def __init__(self, master):
        self.top=Toplevel(master)
        self.top.geometry('770x390')
        self.top.title("Preferences")
        self.ipBase = StringVar()
        self.ipBase.set("10.0.0.0/8")
        self.prefProp = {}
        self.terminalType = StringVar()
        self.terminalType.set('xterm')
        self.startCLI = IntVar()
        self.switchType = StringVar()
        self.switchType.set("Open vSwitch Kernel Mode")
        self.ovsOf10=IntVar()
        self.ovsOf10.set(1)
        self.ovsOf11=IntVar()
        self.ovsOf12=IntVar()
        self.ovsOf13=IntVar()
        self.nFlowAddId=IntVar()
        self.setPreferences()

    def changeTerminalType(self,*args):
        self.prefProp['terminalType']=self.terminalType

    def changeSwitchType(self,*args):
        self.prefProp['switchType']=self.switchType

    def setPreferences(self):
        optionsTerminal=['xterm','gterm']
        optionsSwitch=["Open vSwitch Kernel Mode","Indigo Virtual Switch","Userspace Switch","Userspace Switch inNamespace"]
        sampling = StringVar()
        sampling.set("400")
        header=StringVar()
        header.set('128')
        polling=StringVar()
        polling.set("30")
        activeTimeout=StringVar()
        activeTimeout.set("600")

        #IP base
        label_ip=Label(self.top,text="IP base :",width=10,font=("bold",10))
        label_ip.place(x=0,y=10)
        entry_ip=Entry(self.top,textvariable=self.ipBase)
        entry_ip.place(x=150,y=10)
        self.prefProp['ipBase']=entry_ip

        #terminalType
        labelTerminal=Label(self.top,text="Default Terminal:",width=17,font=("bold",10))
        labelTerminal.place(x=0,y=40)
        self.prefProp['terminalType']=self.terminalType
        self.terminalType.trace("w",self.changeTerminalType)
        dropDownMenu=OptionMenu(self.top,self.terminalType,optionsTerminal[0],optionsTerminal[1])
        dropDownMenu.place(x=150,y=40)

        #CLI
        labelCLI=Label(self.top,text="Start CLI :",width=10,font=("bold",10))
        labelCLI.place(x=0,y=70)
        boutonCLI=Checkbutton(self.top,variable=self.startCLI)
        boutonCLI.place(x=150,y=70)

        #SwitchType
        labeldefaultSwitch=Label(self.top,text="Default Switch :",width=15,font=("bold",10))
        labeldefaultSwitch.place(x=0,y=100)

        self.prefProp['switchType']=self.switchType
        self.switchType.trace("w",self.changeSwitchType)
        dropDownMenu1=OptionMenu(self.top,self.switchType,optionsSwitch[0],optionsSwitch[1],optionsSwitch[2],optionsSwitch[3])
        dropDownMenu1.place(x=150,y=100)

        #OpenVSwitch
        frame=LabelFrame(self.top,width=350, height=150, text="Open vSwitch")
        frame.place(x=10,y=130)

        #OpenFlow 1.0
        label_openFlow=Label(frame,text="OpenFlow 1.0:")
        label_openFlow.place(x=0,y=10)
        bouton_openFlow=Checkbutton(frame,variable=self.ovsOf10)
        bouton_openFlow.place(x=100,y=10)

        #OpenFlow 1.1
        label_openFlow1=Label(frame,text="OpenFlow 1.1:")
        label_openFlow1.place(x=0,y=40)
        bouton_openFlow1=Checkbutton(frame,variable=self.ovsOf11)
        bouton_openFlow1.place(x=100,y=40)

        #OpenFlow 1.2
        label_openFlow2=Label(frame,text="OpenFlow 1.2:")
        label_openFlow2.place(x=0,y=70)
        bouton_openFlow2=Checkbutton(frame,variable=self.ovsOf12)
        bouton_openFlow2.place(x=100,y=70)

        #OpenFlow 1.3
        label_openFlow3=Label(frame,text="OpenFlow 1.3:")
        label_openFlow3.place(x=0,y=100)
        bouton_openFlow3=Checkbutton(frame,variable=self.ovsOf13)
        bouton_openFlow3.place(x=100,y=100)

        #dpctl port
        label_dpctl=Label(self.top,text='dpctl port:')
        label_dpctl.place(x=40,y=290)
        entry_dpctl=Entry(self.top)
        entry_dpctl.place(x=160,y=290)
        self.prefProp['dpctl']=entry_dpctl

        frame1=LabelFrame(self.top,width=350, height=150, text="sFlow Profile for Open vSwitch")
        frame1.place(x=400,y=10)

        #Target
        labelTarget=Label(frame1,text='Target:')
        labelTarget.place(x=0,y=10)
        entryTarget=Entry(frame1)
        entryTarget.place(x=60,y=10)
        self.prefProp['sFlowTarget']=entryTarget

        #Sampling
        label_sampling=Label(frame1,text='Sampling:')
        label_sampling.place(x=0,y=40)
        entry_sampling=Entry(frame1,textvariable=sampling)
        entry_sampling.place(x=70,y=40)
        self.prefProp['sFlowSampling']=entry_sampling

        #Header
        label_header=Label(frame1,text='Header:')
        label_header.place(x=0,y=70)
        entry_header=Entry(frame1,textvariable=header)
        entry_header.place(x=60,y=70)
        self.prefProp['sFlowHeader']=entry_header

        #Polling
        labelPolling=Label(frame1,text='Polling:')
        labelPolling.place(x=0,y=100)
        entryPolling=Entry(frame1,textvariable=polling)
        entryPolling.place(x=60,y=100)
        self.prefProp['sFlowPolling']=entryPolling

        frame2=LabelFrame(self.top,width=350, height=160, text="NetFlow Profile for Open vSwitch")
        frame2.place(x=400,y=170)
        labelTarget=Label(frame2,text='Target:')
        labelTarget.place(x=70,y=10)
        entryTarget=Entry(frame2)
        entryTarget.place(x=120,y=10)
        self.prefProp['nFlowTarget']=entryTarget

        label_activeTimeout=Label(frame2,text='Active Timeout:')
        label_activeTimeout.place(x=20,y=40)
        entry_activeTimeout=Entry(frame2,textvariable=activeTimeout)
        entry_activeTimeout.place(x=130,y=40)
        self.prefProp['nFlowTimeout']=entry_activeTimeout

        label_idInt=Label(frame2,text='Add ID to Interface:')
        label_idInt.place(x=0,y=70)
        bouton_idInt=Checkbutton(frame2,variable=self.nFlowAddId)
        bouton_idInt.place(x=135,y=70)

        bouton_ok=Button(self.top,text="OK",width=10,command=self.okAction)
        bouton_ok.place(x=280,y=345)
        bouton_cancel=Button(self.top,text="Cancel",width=10,command = lambda : self.top.destroy())
        bouton_cancel.place(x=400,y=345)

    def setResult(self):
        self.result={}
        self.result['dpctl']=self.prefProp['dpctl'].get()
        self.result['sflow']={}
        self.result['sflow']['sflowPolling']=self.prefProp['sFlowPolling'].get()
        self.result['sflow']['sflowHeader']=self.prefProp['sFlowHeader'].get()
        self.result['sflow']['sflowTarget']=self.prefProp['sFlowTarget'].get()
        self.result['sflow']['sflowSampling']=self.prefProp['sFlowSampling'].get()
        self.result['openFlowVersions']={}
        self.result['openFlowVersions']['ovsOf10']=self.ovsOf10.get()
        self.result['openFlowVersions']['ovsOf11']=self.ovsOf11.get()
        self.result['openFlowVersions']['ovsOf12']=self.ovsOf12.get()
        self.result['openFlowVersions']['ovsOf13']=self.ovsOf13.get()
        self.result['ipBase']=self.prefProp['ipBase'].get()
        self.result['terminalType']=self.prefProp['terminalType'].get()
        self.result['switchType']=self.prefProp['switchType'].get()
        self.result['netflow']={}
        self.result['netflow']['nflowTarget']=self.prefProp['nFlowTarget'].get()
        self.result['netflow']['nflowTimeout']=self.prefProp['nFlowTimeout'].get()
        self.result['netflow']['nflowAddId']=self.nFlowAddId.get()
        self.result['startCLI']=self.startCLI.get()

    def okAction(self):
        self.setResult()
        self.top.destroy()

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

class pingPacketWindow(object):

    def __init__(self,master,dict_host,textCanvas,network):
        self.top = Toplevel(master)
        self.top.geometry('300x200')
        self.text = textCanvas
        self.number = StringVar()
        self.net = network
        self.number.set('2')
        self.numbers = []
        self.hostnames = []
        self.dict_hosts = dict_host
        self.sethostnames()
        self.setNumbers()
        self.choosenNumber = [ self.numbers[0] ]
        self.selectedNames = [ self.hostnames[0] , self.hostnames[0] ]
        self.selectedNodes = [ self.dict_hosts[ self.hostnames[0] ] , self.dict_hosts[ self.hostnames[0] ] ]
        self.selectedhost1 = StringVar()
        self.selectedhost1.set(self.hostnames[0])
        self.selectedhost2 = StringVar()
        self.selectedhost2.set(self.hostnames[0])
        self.openWindow()

    def setNumbers(self):
        for i in range(2,31):
            self.numbers.append(i)

    def sethostnames(self):
        for host in self.dict_hosts.keys():
            self.hostnames.append(host)

    def changeFirsthost(self,*args):
        self.selectedNames[0] = self.selectedhost1.get()
        self.selectedNodes[0] = self.dict_hosts[ self.selectedhost1.get() ]

    def changeSecondhost(self,*args):
        self.selectedNames[1] = self.selectedhost2.get()
        self.selectedNodes[1] = self.dict_hosts[ self.selectedhost2.get() ]

    def changeNumber(self,*args):
        self.choosenNumber[0] = self.number.get()

    def openWindow(self):
        numbers = self.numbers
        hosts = self.hostnames
        self.number.trace("w",self.changeNumber)
        self.selectedhost1.trace("w",self.changeFirsthost)
        self.selectedhost2.trace("w",self.changeSecondhost)
        dropDownMenu=OptionMenu(self.top,self.selectedhost1,*hosts)
        dropDownMenu.place(x=0,y=50)
        dropDownMenu1=OptionMenu(self.top,self.selectedhost2,*hosts)
        dropDownMenu1.place(x=60,y=50)
        dropDownMenu2=OptionMenu(self.top,self.number,*numbers)
        dropDownMenu2.place(x=120,y=50)
        bouton=Button(self.top,text='OK',command=self.okAction)
        bouton.place(x=180,y=50)

    def pingPacket(self,hosts,number):
        self.text.config(state='normal')
        self.text.delete('1.0',END)
        h1=self.net.get(hosts[0])
        h2=self.net.get(hosts[1])
        self.text.insert(END,'\nExchanged packets between ' + hosts[0] + ' and '  + hosts[1]+'\n'+'\n')
        result= h1.cmd('ping -c %s %s' % (number[0],h2.IP()))
        self.text.insert(END,result)
        self.text.config(state='disabled')

    def okAction(self):
        self.pingPacket(self.selectedNames,self.choosenNumber)
        self.top.destroy()

class iperfWindow(object):

    def __init__(self,master,dict_host,textCanvas,network):
        self.top = Toplevel(master)
        self.top.geometry('700x700')
        self.text = textCanvas
        self.dict_hosts = dict_host
        self.hostnames=[]
        self.sethostnames() #setting hostnames
        self.host1 = StringVar() #var_name2
        self.host1.set(self.hostnames[0])
        self.host2 = StringVar() #var_name3
        self.host2.set(self.hostnames[0])
        self.selectedNames = [self.hostnames[0],self.hostnames[0]] #selectedNames
        self.selectedNodes = [ self.dict_hosts[ self.hostnames[0] ] , self.dict_hosts[ self.hostnames[0] ] ] #selectedNodes
        self.openWindow()

    def sethostnames(self):
        for host in self.dict_hosts.keys():
            self.hostnames.append(host)

    def changeFirsthostname(self,*args):
        self.selectedNames[0] = self.host1.get()
        self.selectedNodes[0] = self.dict_hosts[self.host1.get()]

    def changeSecondhostname(self,*args):
        self.selectedNames[1] = self.host2.get()
        self.selectedNodes[1] = self.dict_hosts[self.host2.get()]

    def openWindow(self):
        namehosts = self.hostnames
        self.host1.trace("w",self.changeFirsthostname)
        self.host2.trace("w",self.changeSecondhostname)
        dropDownMenu=OptionMenu(self.top,self.host1,*namehosts)
        dropDownMenu.place(x=350,y=110)

        dropDownMenu1=OptionMenu(self.top,self.host2,*namehosts)
        dropDownMenu1.place(x=500,y=110)

        bouton =  Button(self.top,text='OK',command = self.okAction)
        bouton.place(x=300,y=600)

    def iperf( self, hosts=None, l4Type='TCP', udpBw='10M' ):
        self.text.config(state='normal')
        self.text.delete('1.0',END)
        if not quietRun( 'which telnet' ):
            self.text.insert(INSERT, 'Cannot find telnet in $PATH - required for iperf test')
            self.text.config(state='disabled')
            return
        client, server = hosts
        self.text.insert(INSERT,'*** Iperf : testing ' + l4Type + ' bandwidth between ' + str(client.name) + ' and ' + str(server.name) + '\n')
        server.cmd( 'killall -9 iperf' )
        iperfArgs = 'iperf '
        bwArgs = ''
        if l4Type == 'UDP':
            iperfArgs += '-u '
            bwArgs = '-b ' + udpBw + ' '
        elif l4Type != 'TCP':
            self.text.insert(INSERT,'Unexpected l4 type: ' + str(l4Type))
            self.text.config(state='disabled')
            return
        server.sendCmd( iperfArgs + '-s', printPid=True )
        servout = ''
        while server.lastPid is None:
            servout += server.monitor()
        while 'Connected' not in client.cmd('sh -c "echo A | telnet -e A %s 5001"' % server.IP()):
            sleep(.5)
        cliout = client.cmd( iperfArgs + '-t 5 -c ' + server.IP() + ' ' + bwArgs )
        server.sendInt()
        servout += server.waitOutput()
        r = r'([\d\.]+ \w+/sec)'
        m = re.findall(r,servout)
        if m:
            iperfservout=m[-1]
        else:
            self.text.insert(INSERT,'could not parse iperf output: ' + servout )
            iperfservout = ''

        r = r'([\d\.]+ \w+/sec)'
        m1 = re.findall(r,cliout)
        if m1:
            iperfcliout=m1[-1]
        else:
            self.text.insert(INSERT,'could not parse iperf output: ' + cliout )
            iperfcliout = ''
        result = [iperfservout,iperfservout]
        if l4Type == 'UDP':
            result.insert( 0, udpBw )
        self.text.insert(INSERT,'*** Results: ' + str(result) + '\n')
        self.text.config(state='disabled')
        return result

    def okAction(self):
        self.iperf(self.selectedNodes)
        self.top.destroy()

class ifconfigWindow(object):

    def __init__(self,master,dict_host,dict_switch,dict_ctrl,textCanvas,net): #self.name_host , self.nameswitch ,self.namecontroller
        self.top=Toplevel(master)
        self.top.geometry('300x130')
        self.network = net
        self.dict_hosts = dict_host
        self.text = textCanvas
        self.dict_switches = dict_switch
        self.dict_ctrls = dict_ctrl
        self.namehosts = []
        self.namectrl = []
        self.nameswitch= []
        self.sethosts()
        self.setCtrls()
        self.setSwitches()
        self.names = self.namehosts + self.namectrl + self.nameswitch
        self.selectedNode = [self.names[0]]
        self.node = StringVar()
        self.node.set(self.names[0])
        self.chooseNode()

    def sethosts(self):
        for hostname in self.dict_hosts.keys():
            self.namehosts.append(hostname)

    def setCtrls(self):
        for ctrl in self.dict_ctrls.keys():
            self.namectrl.append(ctrl)

    def setSwitches(self):
        for switch in self.dict_switches.keys():
            self.nameswitch.append(switch)

    def chooseNode(self):
        helv36 = Font(family='Helvetica', size=10, weight='bold')
        label = Label(self.top,text='Nodes interfaces',font=helv36)
        label.place(x=100,y=0)
        self.node.trace("w",self.changeNodeName)
        names = self.names
        labelChooseNode=Label(self.top,text='Choose node',font=helv36)
        labelChooseNode.place(x=110,y=30)
        dropDownMenu=OptionMenu(self.top,self.node,*names)
        dropDownMenu.place(x=85,y=60)
        bouton = Button(self.top,text='OK',command=self.okAction)
        bouton.place(x=175,y=60)

    def changeNodeName(self,*args):
        self.selectedNode[0] = self.node.get()

    def ifconfigTest(self):
        self.text.config(state='normal')
        self.text.delete('1.0',END)
        self.text.insert(END,"\n" + str(self.selectedNode[0]) + "'s interfaces\n"+'\n' + '\n','big')
        result1=self.network.get(self.selectedNode[0])
        result2=result1.cmd('ifconfig')
        self.text.insert(END,result2,'police')
        self.text.config(state='disabled')

    def okAction(self):
        self.ifconfigTest()
        self.top.destroy()

class pingWindow(object):

    def __init__(self,master,dict_host,textCanvas): #self.name_host , textcanvas
        self.top=Toplevel(master)
        self.top.geometry('300x150')
        self.text = textCanvas
        self.dict_hosts = dict_host  #dictionnaire nom , noeud correspondants
        self.hostnames = [] #liste des hostnames
        self.namesPair = []
        self.nodesPair = []
        self.sethostnames() # set la liste des hostnames
        self.host1 = StringVar()
        self.host2 = StringVar()
        self.host1.set(self.hostnames[0])
        self.host2.set(self.hostnames[0])
        self.openWindow()

    def sethostnames(self):
        for host in self.dict_hosts.keys():
            self.hostnames.append(host)
        self.namesPair = [ self.hostnames[0] , self.hostnames[0] ] # les noms des hotes choisis qu'il faut mettre au départ à hostnames[0]
        self.nodesPair = [ self.dict_hosts[ self.namesPair[0] ] , self.dict_hosts[ self.namesPair[1] ] ] # les noeuds des hotes choisies

    def openWindow(self):
        helv36 = Font(family='Helvetica', size=10, weight='bold')
        label_nodes=Label(self.top,text='Available nodes',font=helv36)
        label_nodes.place(x=100,y=0)

        label_choose=Label(self.top,text='Choose nodes',font=helv36)
        label_choose.place(x=110,y=30)

        names = self.hostnames

        self.host1.trace("w",self.changeFirsthostname)
        self.host2.trace("w",self.changeSecondhostname)

        dropDownMenu=OptionMenu(self.top,self.host1,*names)
        dropDownMenu.place(x=85,y=60)
        dropDownMenu1=OptionMenu(self.top,self.host2,*names)
        dropDownMenu1.place(x=175,y=60)
        bouton = Button(self.top,text='OK',command=self.okAction)
        bouton.place(x=135,y=100)

    def changeFirsthostname(self,*args):
        self.namesPair[0] = self.host1.get()
        self.nodesPair[0] = self.dict_hosts[self.host1.get()]

    def changeSecondhostname(self,*args):
        self.namesPair[1] = self.host2.get()
        self.nodesPair[1] = self.dict_hosts[self.host2.get()]

    def okAction(self):
        self.pingPair(self.nodesPair)
        self.top.destroy()

    def pingPair(self,hosts=None,timeout=None ):
        self.text.config(state='normal')
        self.text.delete('1.0',END)
        self.text.insert(END,'\nPing : Testing ping reachability between ' + str(hosts[0]) + ' and ' + str(hosts[1]) + '\n\n','modif')
        packets = 0
        lost = 0
        ploss = None
        for node in hosts:
            self.text.insert(END,str(node.name) + ' ' + '-> ','police')
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
                                self.text.insert(END,'*** Error: could not parse ping output: ' + str(result) + '\n','police')
                                (sent,received)=(1,0)
                            else:
                                (sent,received) = (int(m.group(1)),int(m.group(2)))
                    else:
                        sent, received = 0, 0
                    packets += sent
                    if received > sent:
                        self.text.insert(END,'*** Error: received too many packets','police')
                        self.text.insert(INSERT,str(result))
                        node.cmdPrint('route')
                        exit(1)
                    lost += sent - received
                    if received :
                        self.text.insert(INSERT,str(dest.name),'police1')
                    else:
                        self.text.insert(INSERT,str('X'),'police1')
            self.text.insert(INSERT,str('\n'))
        if packets > 0:
            ploss = 100.0 * lost / packets
            received = packets - lost
            self.text.insert(END,"*** Results: "+str(ploss)+' '+'dropped ('+str(received)+'/'+str(packets)+'received)\n','police')
        else:
            ploss = 0
            self.text.insert(END,"*** Warning: No packets sent\n",'police')
        self.text.config(state='disabled')
        return ploss

class ipaWindow(object):

    def __init__(self, master,dict_switches,dict_hosts,textCanvas):
        self.text = textCanvas
        self.top=Toplevel(master)
        self.top.geometry('200x200')
        self.dict_switch = dict_switches
        self.dict_host = dict_hosts
        self.listOfNodes = None
        self.selectedNode = []
        self.node = StringVar()
        self.chooseNode()

    def dict_switch_keys(self):
        name_switch = []
        for name in self.dict_switch.keys():
            name_switch.append(name)
        return name_switch

    def dict_host_keys(self):
        name_host = []
        for name in self.dict_host.keys():
            name_host.append(name)
        return name_host

    def changeNode(self,*args):
        self.selectedNode[0]=self.node.get()

    def chooseNode(self):
        list_switches = self.dict_switch_keys()
        list_hosts = self.dict_host_keys()
        self.listOfNodes = list_switches + list_hosts
        self.node.set(self.listOfNodes[0])
        self.node.trace('w',self.changeNode)
        self.selectedNode = [self.listOfNodes[0]]
        listNodes = self.listOfNodes
        dropdownmenu = OptionMenu(self.top,self.node,*listNodes)
        dropdownmenu.place(x=20,y=30)
        bouton=Button(self.top,text='OK',command=partial(self.ipa,self.selectedNode))
        bouton.place(x=80,y=30)

    def ipa(self,names):
        self.top.destroy()
        self.text.config(state="normal")
        self.text.delete('1.0',END)

        if names[0] in self.dict_switch.keys() :
            node = self.dict_switch[names[0]]
            links, _err, _result = node.pexec( 'ip link show' )
            self.text.insert(END,links)
            self.text.config(state='disabled')
            return
        elif names[0] in self.dict_host.keys():
            node = self.dict_host[names[0]]
            links, _err, _result = node.pexec('ip link show')
            self.text.insert(END,links)
            self.text.config(state='disabled')


class serverOrClient(object):

    def __init__(self,master,dict_host):
        self.top = Toplevel(master)
        self.top.geometry('1000x1000')
        self.clients=[]
        self.servers=[]
        self.hostnames=[]
        self.courbes=[]
        self.liste=[]
        self.listNameservers = []
        self.listNameclients = []
        self.entries_server = []
        self.entriesClient = []
        self.listProtocol = []
        self.protocols = []
        self.canvas = Canvas(self.top,width=1000,height=1000,bg='snow')
        self.canvas.grid(row=0, column=0)
        self.dict_hosts = dict_host
        self.variables_server = []
        self.clientserver = []
        self.iperfwindow()

    def plots(self):
        variable=IntVar()
        for i in range(0,len(self.dict_hosts)):
            self.courbes.append([])
        for j in range(0,len(self.dict_hosts)):
            self.courbes[j].append(variable)

    def server(self):
        for i in range(0,len(self.dict_hosts)):
            variable = StringVar()
            variable.set(self.hostnames[0])
            self.servers.append(variable)

    def client(self):
        for i in range(0,len(self.dict_hosts)):
            self.clients.append([])

        for i in range(0,len(self.clients)):
            for j in range (0,len(self.dict_hosts)):
                variable = IntVar()
                self.clients[j].append(variable)

    def names(self):
        for name in self.dict_hosts.keys():
            self.hostnames.append(name)

    def setvariables(self):
        for i in range (0,len(self.dict_hosts)):
            self.variables_server.append(self.hostnames[0])

    def changeserver(self,i,*args):
        self.variables_server[i] = self.servers[i].get()

    def create_dict(self,*args):

        for i in range(0,len(self.dict_hosts)):
            dict = {}
            dict['serverNode'] = self.dict_hosts[self.variables_server[i]]
            dict['serverName'] = self.variables_server[i]
            dict['clientNodes'] = []
            dict['clientNames'] = []

            for j in range(0,len(self.dict_hosts)):
                if(self.clients[i][j].get() == 1):
                    dict['clientNodes'].append(self.dict_hosts[self.hostnames[j]])
                    dict['clientNames'].append(self.hostnames[j])

            self.clientserver.append(dict)

        listClients = []
        for dict in self.clientserver :
            if(dict['clientNodes'] != []):
                for i in range(0,len(dict['clientNodes'])):
                    self.liste.append({'serverName' : dict['serverName'] , 'infos' : [ dict['serverNode'] , dict['serverName'], dict['clientNodes'][i] , dict['clientNames'][i] ] })
                    listClients.append(dict['clientNames'][i])
                self.listNameclients.append( {'serverName': dict['serverName'] , 'client' : listClients } )
                listClients=[]
                self.listNameservers.append(dict['serverName'])

        for i in range(0,len(self.listNameservers)):
            variable = StringVar()
            variable.set('TCP')
            self.listProtocol.append({'serverName' : self.listNameservers[i] , 'protocolvalue' : 'TCP' })
            self.protocols.append({'serverName': self.listNameservers[i] , 'protocol' : variable})

    def placetext(self,top):

        canvas = Canvas(top,width=100,height=100)
        canvas.place(x='10',y='10')
        texte = Text(canvas)
        scroll = Scrollbar(canvas,command=texte.yview)
        texte.configure(yscrollcommand=scroll.set)
        texte.config(state="normal")
        texte.pack(side=LEFT)
        scroll.pack(side=RIGHT,fill=Y)
        return texte

    def changeProtocol(self,serverName,*args):
        #pour changer le protocole correspondant
        for dict in self.protocols :
            if(dict['serverName'] == serverName):
                varControle = dict['protocol']
                break

        for dict in self.listProtocol :
            if(dict['serverName'] == serverName):
                dict['protocolvalue'] = varControle.get()
                break

        print(self.listProtocol)

    def properties(self,serverName):
        root = Toplevel()
        root.geometry('500x800')

        rootClients = []
        dicts = []

        rootOutput = Toplevel()
        rootOutput.geometry('600x600')
        texte = self.placetext(rootOutput)

        for element in self.liste :
            if(element['serverName'] == serverName):
                dicts.append(element)

        for element in self.protocols :
            if (element['serverName'] == serverName):
                protocol = element['protocol']
                break

        listProtocol=['TCP','UDP']
        helv36 = Font(family='Helvetica', size=10, weight='bold')

        #labelProperties=Label(dicts[0]['infos'][0],text='Server Properties' + ' for ' + serverName,font=helv36)
        labelProperties=Label(root,text='Server Properties' + ' for ' + serverName,font=helv36)
        labelProperties.place(x=10,y=10)

        labelInterval=Label(root,text="Interval to display a report on bw (-i)")
        labelInterval.place(x=10,y=65)
        entryInterval=Entry(root,width=10)
        entryInterval.place(x=260,y=65)

        labelPort = Label(root,text="Port")
        labelPort.place(x=10,y=95)
        entryPort=Entry(root,width=10)
        entryPort.place(x=260,y=95)

        labelProtocol = Label(root,text="Protocol")
        labelProtocol.place(x=10,y=125)
        protocol.trace("w",partial(self.changeProtocol,serverName))
        dropDownMenu=OptionMenu(root,protocol,*listProtocol)
        dropDownMenu.place(x=260,y=125)

        labelFilename = Label(root,text="Choose a file name")
        labelFilename.place(x=10,y=155)
        entryFilename=Entry(root,width=10)
        entryFilename.place(x=260,y=155)

        self.entries_server.append({'server': serverName , 'intervalEntry': entryInterval , 'portEntry' : entryPort , 'fileEntry' : entryFilename})

        ord = 215
        for i in range(0,len(dicts)): # nombre de clients
            labelClient=Label(root, text = 'Client ' + dicts[i]['infos'][3] + " 's Properties",font=helv36)
            labelClient.place(x=10,y=ord)

            labelBandwidth = Label(root,text='Bandwidth')
            labelBandwidth.place(x=10,y=ord+60)
            entryBandwidth=Entry(root,width=10)
            entryBandwidth.place(x=120,y=ord+60)

            labelTest = Label(root,text='Test duration')
            labelTest.place(x=10,y=ord+90)
            entryTest=Entry(root,width=10)
            entryTest.place(x=120,y=ord+90)
            dictClient = {'serverName' : dicts[i]['serverName'] , 'clientName' : dicts[i]['infos'][3] , 'clientEntries' : [entryBandwidth,entryTest]}
            self.entriesClient.append(dictClient)
            bouton = Button(root,text='Test iperf',command = partial(self.iperf,texte,[ self.dict_hosts[ dicts[i]['infos'][3] ] , self.dict_hosts[serverName] ], protocol , entryBandwidth , entryTest , entryPort , entryInterval , entryFilename ) )
            bouton.place(x=10,y=ord+120)
            ord += 150

        bouton = Button(root,text='Finish',command = lambda : root.destroy())
        bouton.place(x=10,y=ord+30)

    def iperfwindow(self):
        setLogLevel('info')
        self.names() # met à jour self.hostnames
        self.client() # met à jour self.clients #IntVar
        self.server() # met à jour self.servers #StringVar on les as tous settées à hostnames[0] il faut mettre set_trace
        self.plots() # met à jour self.courbes
        self.setvariables()
        hostnames = self.hostnames

        abscisse = 10
        ordonnee = 10

        abscisse_server = 10
        ordonnees_server = 10

        for i in range (0,len(self.dict_hosts)):
            label_server = Label(self.canvas,text='server',font=("bold",10))
            label_server.place(x=abscisse_server,y=ordonnees_server)
            self.servers[i].trace("w",partial(self.changeserver,i))
            dropDownMenu=OptionMenu(self.canvas,self.servers[i],*hostnames)
            dropDownMenu.place(x=abscisse_server,y=ordonnees_server+30)
            self.canvas.create_line((0,ordonnees_server+70),(1500,ordonnees_server+70))
            ordonnees_server += 80

        for j in range (0,len(self.dict_hosts)): #On passe à un autre serveur
            for i in range (0,len(self.dict_hosts)):
                label_client = Label(self.canvas,text=hostnames[i],font=("bold",10))
                label_client.place(x=abscisse+100,y=ordonnee)
                bouton = Checkbutton(self.canvas,variable=self.clients[j][i])
                bouton.place(x=abscisse+180,y=ordonnee)
                abscisse += 160
            ordonnee += 80
            abscisse = 10

        bouton_ok=Button(self.top,text='OK',width=10,command=self.okAction)
        bouton_ok.place(x=300,y=300)

    def okAction(self):
        self.create_dict()

        for server in self.listNameservers :
            self.properties(server)

        self.top.destroy()

    def find_key(self,v,dict):
        for k, val in dict.items():
            if v == val:
                return k

    def iperf( self,textserver, hosts, l4Type, udpBw,seconds,port,timeServer,fichier):
        #rootserver = Toplevel()
        #rootserver.geometry('600x600')
        rootclient = Toplevel()
        rootclient.geometry('600x600')
        #textserver = self.placetext(rootserver)
        textclient = self.placetext(rootclient)
        client, server = hosts
        [clientName,serverName] = [self.find_key(client,self.dict_hosts),self.find_key(server,self.dict_hosts)]
        textclient.insert(INSERT,'*** Iperf: testing '+str(l4Type.get())+' bandwidth between '+str(client.name)+ ' and '+str(server.name)+ '\n')
        server.cmd( 'killall -9 iperf' )
        port1 = port.get()
        port1 = int(port1)

        #serveur
        iperfArgs = 'iperf -p %d' % port1
        timeServer1 = int(timeServer.get())
        iperfArgs += ' -i %s '% timeServer1
        bwArgs = '-b ' + udpBw.get() + ' '
        if l4Type.get() == 'UDP':
             iperfArgs += '-u '
             bwArgs = '-b ' + udpBw.get() + ' '
        elif l4Type.get() != 'TCP':
              textclient.insert(INSERT,'Unexpected l4 type : ' + l4Type.get())
              #textclient.config(state='disabled')
              return
        server.sendCmd(iperfArgs + '-s')
        iperfArgs1='iperf -p %d ' % port1
        bwArgs1 = '-b ' + udpBw.get() + ' '
        if l4Type.get() == 'UDP':
             iperfArgs1 += '-u '
             bwArgs1 = '-b ' + udpBw.get() + ' '
        elif l4Type.get() != 'TCP':
              textclient.insert(INSERT,'Unexpected l4 type : ' + l4Type.get())
              #textclient.config(state='disabled')
              return

        if l4Type.get() == 'TCP':
            if not waitListening( client, server.IP(), port1):
                textclient.insert(INSERT,'Could not connect to iperf on port ' + port.get())
                return
        seconds1 = int(seconds.get())
        cliout = client.cmd( iperfArgs1 + '-t %d -c ' % seconds1 + server.IP() + ' ' + bwArgs1)
        textclient.insert(INSERT,'Client output: ' + cliout + '\n')

        servout = ''
        count = 2 if l4Type.get() == 'TCP' else 1
        while len( re.findall( '/sec', servout ) ) < count:
            servout += server.monitor( timeoutms=5000 )
        server.sendInt()
        servout += server.waitOutput()
        textserver.insert(INSERT,'Server output: ' + servout + '\n')
        fileName = open(fichier.get(),'w')
        fileName.write(servout)
        fileName.close()
        if(l4Type.get() == 'TCP'):

            file = open(fichier.get(),'r')
            lines = file.readlines()
            for line in lines:
                if 'sec' not in line:
                    lines.remove(line)

            for i in range(0,4):
                lines.remove(lines[0])

            for j in range(0,len(lines)):
                lines[j]=lines[j][6:38]

            lines.remove(lines[len(lines)-1])

            abscisse = []
            ordonnee = []

            for j in range(0,len(lines)):
                abscisse.append(float(lines[j][5:9]))
                ordonnee.append(float(lines[j][27:32]))

            plt.plot(abscisse,ordonnee,label='client : ' + clientName + ', server : ' + serverName)
            plt.axis([min(abscisse),max(abscisse)+1,0, max(ordonnee)+1])
            plt.xlabel('time')
            plt.ylabel('bandwidth')
            plt.legend()
            plt.show()

            file.close()

        elif(l4Type.get() == 'UDP'):
            file2=open(fichier.get(),'r')
            lines2 = file2.readlines()
            for line in lines2:
                if 'sec' not in line:
                    lines2.remove(line)

            for i in range(0,3):
                 lines2.remove(lines2[0])

            lines2.remove(lines2[4])
            lines2.remove(lines2[len(lines2)-1])

            for j in range(0,len(lines2)):
                lines2[j]=lines2[j][6:38]

            lines2.remove(lines2[1])

            abscisse2=[]
            ordonnee2=[]
            for j in range(0,len(lines2)):
                abscisse2.append(float(lines2[j][5:9]))
                ordonnee2.append(float(lines2[j][27:32]))

            plt.plot(abscisse2,ordonnee2)
            plt.axis([min(abscisse2),max(abscisse2)+1,0, max(ordonnee2)+1])
            plt.xlabel('time')
            plt.ylabel('bandwidth')
            plt.show()

            file2.close()

class Interface():

    def __init__(self,window):
        self.window = window
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
        self.performances = ['Links','Iperf','Ping','Ifconfig','ip -a']
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
        #self.create_buttons(window)

        self.s = ttk.Style()
        #self.s.configure('TFrame', background='yellow')

        self.s.configure('Frame1.TFrame',background='red')
        self.s.configure('Frame2.TFrame',background='blue')
        self.s.configure('Frame3.TFrame',background='snow')

        self.systemOnglet = ttk.Notebook(window,width=1500)
        self.systemOnglet.place(x='0',y='0')

        self.firstOnglet = ttk.Frame(self.systemOnglet,width=1500,height=1500,style='Frame1.TFrame')
        self.firstOnglet.place(x='0',y='0')
        self.systemOnglet.add(self.firstOnglet,text='Topologie')
        self.canvas1 = self.create_canvas_first(self.firstOnglet)

        self.secondOnglet = ttk.Frame(self.systemOnglet,width=1500,height=1500,style='Frame2.TFrame')
        self.secondOnglet.place(x='30',y='0')
        self.systemOnglet.add(self.secondOnglet,text='Tests de performance')
        self.canvas2 = self.create_canvas_second(self.secondOnglet)

        self.thirdOnglet = ttk.Frame(self.systemOnglet,width=1500,height=1500,style='Frame3.TFrame')
        self.thirdOnglet.place(x='60',y='0')
        self.systemOnglet.add(self.thirdOnglet,text='Contrôleurs SDN')
        self.canvas3 = self.create_canvas_third(self.thirdOnglet)

        self.canvas_buttons=self.create_canvas_buttons(self.canvas1)
        self.create_buttons(self.canvas_buttons)
        self.canvas_performances = self.create_canvas_performances(self.canvas2)
        self.create_buttons_performances(self.canvas_performances)

        # Canvas for text
        self.canvas_text = self.create_canvas_text(self.canvas2)
        self.textCanvas = Text(self.canvas_text)
        self.placeText()

    def selectedNode(self):
        return self.selectedNode

    def hostOptions(self):
        return self.hostOptions

    def placeText (self):
        scroll = Scrollbar(self.canvas_text,command=self.textCanvas.yview)
        self.textCanvas.configure(yscrollcommand=scroll.set)
        self.textCanvas.config(state="normal")
        self.textCanvas.pack(side=LEFT)
        self.textCanvas.tag_configure('modif',justify='center',font=('Helvetica',12,'bold'),foreground='RoyalBlue1',underline=1)
        self.textCanvas.tag_configure('police',justify='center',font=('Helvetica',12,'bold'))
        self.textCanvas.tag_configure('police1',font=('Helvetica',12,'bold'))
        self.textCanvas.tag_configure('colour',font=('Helvetica',16,'bold'),spacing1=30)
        self.textCanvas.tag_configure('big',justify='center',font=('Helvetica',16,'bold'),foreground='RoyalBlue1',underline=1)
        scroll.pack(side=RIGHT,fill=Y)

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
        sousmenu2.add_command(label="Preferences",font=helv36,command=self.prefdetails)
        mainmenu.add_cascade(label='Edit',menu=sousmenu2,font=helv36)

        sousmenu3=Menu(mainmenu,bg='white',font=helv36,tearoff=0)
        sousmenu3.add_command(label="Run",font=helv36)
        sousmenu3.add_command(label="Stop",font=helv36)
        sousmenu3.add_command(label="Show OVS Summary",font=helv36,command=self.ovsShow)
        sousmenu3.add_command(label="Root Terminal",font=helv36,command=self.display_shell)
        mainmenu.add_cascade(label='Run',menu=sousmenu3,font=helv36)

        sousmenu4=Menu(mainmenu,bg='white',tearoff=0)
        #sousmenu4.add_command(label="Net",font=helv36,command=self.dumpNet)
        #sousmenu4.add_command(label="Ifconfig",font=helv36,command=self.chooseNode)
        #sousmenu4.add_command(label="Ping all hosts",font=helv36,command=self.pinghosts)
        #sousmenu4.add_command(label="Ping pair",font=helv36,command=self.pingpair)
        #sousmenu4.add_command(label="Iperf",font=helv36,command=self.iperf_test)
        #sousmenu4.add_command(label="List of Nodes",font=helv36,command=self.listNodes)
        sousmenu4.add_command(label="Nodes and links informations",font=helv36,command=self.node_info)
        #sousmenu4.add_command(label="Ping packet",font=helv36,command=self.pingpacket)
        sousmenu4.add_command(label='Preferences informations',font=helv36,command=self.preferencesinformations)
        #sousmenu4.add_command(label='ip a',font=helv36,command=self.ipa)
        #sousmenu4.add_command(label='links',font=helv36,command=self.linkinfo)
        #sousmenu4.add_command(label='Choose server and client',font=helv36,command=self.chooseServerClient)
        mainmenu.add_cascade(label='Command',font=helv36,menu=sousmenu4)

        sousmenu5=Menu(mainmenu,bg='white',tearoff=0)
        sousmenu5.add_command(label="About NetView",font=helv36)
        mainmenu.add_cascade(label='Help',font=helv36,menu=sousmenu5)

        window.config(menu=mainmenu)

    def create_canvas_text(self,window):
        canvas = Canvas(window,width=500,height=500,bg='gray')
        canvas.place(x='150',y='50')
        return canvas

    def create_canvas_buttons(self,window):
        canvas = Canvas(window,width='56',height='1500',bg='white')
        canvas.place(x='0',y='0')
        return canvas

    def create_canvas_performances(self,window):
        canvas = Canvas(window,width='120',height='1500',bg='white')
        canvas.place(x='0',y='0')
        return canvas

    def create_canvas_first(self,window):
        #canvas = Canvas(window,width='1000',height='1000',bg='pink')
        canvas = Canvas(window,width='1500',height='1500',bg='SlateGray1')
        canvas.place(x='0',y='0')
        canvas.bind('<ButtonPress-1>',self.canvasHandle)
        #canvas.bind('<B1-Motion>',self.dragCanevas)
        #canvas.bind('<ButtonRelease-1>',self.dropCanevas)
        return canvas

    def create_canvas_second(self,window):
        #canvas = Canvas(window,width='1000',height='1000',bg='pink')
        canvas = Canvas(window,width='1500',height='1500',bg='SlateGray1')
        canvas.place(x='0',y='0')
        ##canvas.bind('<ButtonPress-1>',self.canvasHandle)
        #canvas.bind('<B1-Motion>',self.dragCanevas)
        #canvas.bind('<ButtonRelease-1>',self.dropCanevas)
        return canvas

    def create_canvas_third(self,window):
        #canvas = Canvas(window,width='1000',height='1000',bg='pink')
        canvas = Canvas(window,width='1500',height='1500',bg='SlateGray1')
        canvas.place(x='0',y='0')
        ##canvas.bind('<ButtonPress-1>',self.canvasHandle)
        #canvas.bind('<B1-Motion>',self.dragCanevas)
        #canvas.bind('<ButtonRelease-1>',self.dropCanevas)
        return canvas

    def create_canvas(self,window):
        #canvas = Canvas(window,width='1000',height='1000',bg='pink')
        canvas = Canvas(window,width='1500',height='1500',bg='SlateGray1')
        canvas.place(x='55',y='0')
        #canvas.bind('<ButtonPress-1>',self.canvasHandle)
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

    def listNodes(self):
        self.textCanvas.config(state='normal')
        self.textCanvas.delete('1.0',END)
        self.textCanvas.insert(END,'\nAvailable nodes\n','big')
        for i in range(0,len(self.names)):
            self.textCanvas.insert( END , self.names[i] + ' ','colour')
        self.textCanvas.config(state='disabled')


    def pinghosts(self,hosts=None,timeout=None ):
        self.textCanvas.config(state='normal')
        self.textCanvas.delete('1.0',END)
        packets = 0
        lost = 0
        ploss = None
        if not hosts:
            hosts = self.hosts
            self.textCanvas.insert(END,'\n\n*** Ping: testing ping reachability between hosts\n\n')
        for node in hosts:
            self.textCanvas.insert(END,str(node.name) + ' ' + '-> ')
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
                                self.textCanvas.insert(END,'*** Error: could not parse ping output: ' + str(result) + '\n')
                                (sent,received)=(1,0)
                            else:
                                (sent,received) = (int(m.group(1)),int(m.group(2)))
                    else:
                        sent, received = 0, 0
                    packets += sent
                    if received > sent:
                        self.textCanvas.insert(END,'*** Error: received too many packets')
                        self.textCanvas.insert(INSERT,str(result))
                        node.cmdPrint('route')
                        exit(1)
                    lost += sent - received
                    if received :
                        self.textCanvas.insert(INSERT,str(dest.name))
                    else:
                        self.textCanvas.insert(INSERT,str('X'))
            self.textCanvas.insert(INSERT,str('\n'))
        if packets > 0:
            ploss = 100.0 * lost / packets
            received = packets - lost
            self.textCanvas.insert(END,"*** Results: "+str(ploss)+' '+'dropped ('+str(received)+'/'+str(packets)+'received)\n')
        else:
            ploss = 0
            self.textCanvas.insert(END,"*** Warning: No packets sent\n")
        self.textCanvas.config(state='disabled')
        return ploss

    def linkInfo(self):
        self.textCanvas.config(state='normal')
        self.textCanvas.delete('1.0',END)
        listlinks=[]
        for link in self.links.keys():
            if(self.links[link]['type'] == 'data'):
                src=self.net.get(self.links[link]['src'])
                dst=self.net.get(self.links[link]['dest'])
                linkss=self.net.linksBetween(src,dst)
                listlinks.append(linkss)
        for link2 in listlinks:
            self.textCanvas.insert(INSERT,link2[0].__str__())
            self.textCanvas.insert(INSERT,link2[0].status())
            self.textCanvas.insert(INSERT,'\n')
        self.textCanvas.config(state='disabled')

    def create_buttons(self,window):
        abs=0;
        ord=10;
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

    def create_buttons_performances(self,window):
        helv36 = Font(family='Helvetica', size=10, weight='bold')
        boutonLink=Button(window,width=5,height=2,bg='white',text='Links',font=helv36,command=self.linkInfo)
        boutonLink.place(x='5',y='10')
        boutonNet=Button(window,width=5,height=2,bg='white',text='Net',font=helv36,command=self.dumpNet)
        boutonNet.place(x='5',y='70')
        boutonIpa=Button(window,width=5,height=2,bg='white',text='ipa',font=helv36,command=self.commandIpa)
        boutonIpa.place(x='5',y='130')
        boutonPinghosts = Button(window,width=5,height=2,bg='white',text='ping hosts',font=helv36,command=self.pinghosts)
        boutonPinghosts.place(x='5',y='190')
        boutonPingpair = Button(window,width=5,height=2,bg='white',text='ping pair',font=helv36,command=self.pingpair)
        boutonPingpair.place(x='5',y='250')
        boutonNodes = Button(window,width=5,height=2,bg='white',text='Nodes',font=helv36,command=self.listNodes)
        boutonNodes.place(x='5',y='310')
        boutonIfconfig = Button(window,width=5,height=2,bg='white',text='Ifconfig',font=helv36,command=self.ifconfig)
        boutonIfconfig.place(x='5',y='370')
        boutonPingPacket = Button(window,width=5,height=2,bg='white',text='Ping Packet',font=helv36,command=self.pingPacket)
        boutonPingPacket.place(x='5',y='430')
        boutonIperf = Button(window,width=5,height=2,bg='white',text='Iperf',font=helv36,command=self.iperf)
        boutonIperf.place(x='5',y='490')
        boutonserver = Button(window,width=5,height=2,bg='white',text='serverOrclient',font=helv36,command=self.iperfserver)
        boutonserver.place(x='5',y='550')

    def iperfserver(self):
        iperfwindow = serverOrClient(self.window,self.name_host)
        self.window.wait_window(iperfwindow.top)

    def ifconfig(self):
        ifconfigwindow = ifconfigWindow(self.window,self.name_host,self.nameswitch,self.namecontroller,self.textCanvas,self.net)
        self.window.wait_window(ifconfigwindow.top)

    def pingpair(self):
        pingwindow= pingWindow(self.window,self.name_host,self.textCanvas)
        self.window.wait_window(pingwindow.top)

    def commandIpa (self) :
        ipawindow = ipaWindow(self.window,self.nameswitch,self.name_host,self.textCanvas)
        self.window.wait_window(ipawindow.top)

    def pingPacket(self):
        pingpacketwindow = pingPacketWindow(self.window,self.name_host,self.textCanvas,self.net)
        self.window.wait_window(pingpacketwindow.top)

    def iperf(self):
        iperfwindow = iperfWindow(self.window,self.name_host,self.textCanvas,self.net)
        self.window.wait_window(iperfwindow.top)

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
            self.canvas1.delete(item)
        for i in range(0,len(self.liens)):
            self.canvas1.delete(self.liens[i])
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
        icon=Button(self.canvas1,image=self.images[nodeName])
        item=self.canvas1.create_window(x,y,anchor='center',window=icon)
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
        #widget.bind("<B1-Motion>", self.drag)
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
         #else:
             #self.on_drag_motion(event)

    def release(self,event):
        if (self.activeButton == "Link"):
            self.finishLink(event)

    def on_drag_start(self,event):
        widget = event.widget
        widget._drag_start_x = event.x
        widget._drag_start_y = event.y

    def on_drag_motion(self,event):
        widget = event.widget
        item=self.widgetToItem[widget]
        x1,y1=self.canvas1.coords(item)
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
                popup_menu=Menu(self.canvas1,tearoff=0)
                popup_menu.add_command(label="Terminal",command=self.xterm)
                popup_menu.post(event.x_root,event.y_root)
                return
        popup_menu=Menu(self.canvas1,tearoff=0)
        popup_menu.add_command(label="Host Properties",command=self.hostdetails)
        popup_menu.post(event.x_root,event.y_root)

    def switchdetails(self):
        setLogLevel('info')
        name_switch = self.switchOptions[self.selectedNode]['nameSwitch']
        switchwindow = switchWindow(self.window,name_switch)
        self.window.wait_window(switchwindow.top)
        if switchwindow.result:
            newOptions = {'nodeNum':self.switchOptions[self.selectedNode]['numSwitch']}
            newOptions['switchType'] = switchwindow.result['switchType']
            newOptions['controllers'] = self.switchOptions[self.selectedNode]['options']['controllers']
            if len(switchwindow.result['startCommand']) > 0:
                newOptions['startCommand'] = switchwindow.result['startCommand']
            if len(switchwindow.result['stopCommand']) > 0:
                newOptions['stopCommand'] = switchwindow.result['stopCommand']
            if len(switchwindow.result['dpctl']) > 0:
                newOptions['dpctl'] = switchwindow.result['dpctl']
            if len(switchwindow.result['dpid']) > 0:
                newOptions['dpid'] = switchwindow.result['dpid']
            if len(switchwindow.result['hostname']) > 0:
                newOptions['hostname'] = switchwindow.result['hostname']
            if len(switchwindow.result['externalInterfaces']) > 0:
                newOptions['externalInterfaces'] = switchwindow.result['externalInterfaces']
            newOptions['switchIP'] = switchwindow.result['switchIP']
            newOptions['sflow'] = switchwindow.result['sflow']
            newOptions['netflow'] = switchwindow.result['netflow']
            self.switchOptions[self.selectedNode]['options'] = newOptions
            info( 'New switch details for ' + name_switch + ' = ' + str(newOptions), '\n' )

    def hostdetails(self):
        setLogLevel('info')
        name_host = self.hostOptions[self.selectedNode]['hostname']
        hostwindow = hostWindow(self.window,name_host)
        self.window.wait_window(hostwindow.top)

        if hostwindow.result:
            newOptions = {'nodeNum':self.hostOptions[self.selectedNode]['numhost']}
            newOptions['sched'] = hostwindow.result['sched']
            if len(hostwindow.result['startCommand']) > 0:
                newOptions['startCommand'] = hostwindow.result['startCommand']
            if len(hostwindow.result['stopCommand']) > 0:
                newOptions['stopCommand'] = hostwindow.result['stopCommand']
            if len(hostwindow.result['cpu']) > 0:
                newOptions['cpu'] = float(hostwindow.result['cpu'])
            if len(hostwindow.result['cores']) > 0:
                newOptions['cores'] = hostwindow.result['cores']
            if len(hostwindow.result['hostname']) > 0:
                newOptions['hostname'] = hostwindow.result['hostname']
            if len(hostwindow.result['defaultRoute']) > 0:
                newOptions['defaultRoute'] = hostwindow.result['defaultRoute']
            if len(hostwindow.result['ip']) > 0:
                newOptions['ip'] = hostwindow.result['ip']
            if len(hostwindow.result['externalInterfaces']) > 0:
                newOptions['externalInterfaces'] = hostwindow.result['externalInterfaces']
            if len(hostwindow.result['vlanInterfaces']) > 0:
                newOptions['vlanInterfaces'] = hostwindow.result['vlanInterfaces']
            if len(hostwindow.result['privateDirectory']) > 0:
                newOptions['privateDirectory'] = hostwindow.result['privateDirectory']
            self.hostOptions[self.selectedNode]['options']=newOptions
            info('New host details for ' + newOptions['hostname'] + '=' + str(newOptions) + '\n')

    def ctrldetails(self):
        setLogLevel('info')
        nameCtrl = self.controllerOptions[self.selectedNode]['hostname']
        ctrlwindow = ctrlWindow(self.window,nameCtrl)
        self.window.wait_window(ctrlwindow.top)
        if ctrlwindow.result:
            newOptions = {'controllerType':ctrlwindow.result['controllerType'],'controllerProtocol':ctrlwindow.result['controllerProtocol']}
            if len(ctrlwindow.result['hostname']) > 0:
                newOptions['hostname']= ctrlwindow.result['hostname']
            if len(ctrlwindow.result['remotePort']) > 0:
                newOptions['remotePort']= ctrlwindow.result['remotePort']
            if len(ctrlwindow.result['remoteIP']) > 0:
                newOptions['remoteIP']= ctrlwindow.result['remoteIP']
            self.controllerOptions[self.selectedNode]['options'] = newOptions
            info( 'New controller details for ' + newOptions['hostname'] + ' = ' + str(newOptions), '\n' )

    def linkdetails(self):
        setLogLevel('info')
        linkwindow = linkWindow(self.window)
        self.window.wait_window(linkwindow.top)
        if linkwindow.result is not None:
            self.links[self.selectedLink]['options']=linkwindow.result
            info( 'New link details = ' + str(linkwindow.result), '\n' )

    def prefdetails(self):
        setLogLevel('info')
        prefwindow = prefWindow(self.window)
        self.window.wait_window(prefwindow.top)
        info( 'New Prefs = ' + str(prefwindow.result), '\n' )
        if prefwindow.result:
            self.preferences = prefwindow.result

    def popup_controller(self,event):
        item=event.widget
        self.selectedNode=event.widget
        popup_menu=Menu(self.canvas1,tearoff=0)
        popup_menu.add_command(label="Controller Properties",command=self.ctrldetails)
        popup_menu.post(event.x_root,event.y_root)

    def popup_switch(self,event):
        item=event.widget
        self.selectedNode=event.widget
        for bouton in self.list_buttons.values():
            etat_bouton =str(bouton['state'])
            if etat_bouton == 'disabled':
                popup_menu=Menu(self.canvas1,tearoff=0)
                popup_menu.add_command(label="List Bridge",command=self.listBridge)
                popup_menu.post(event.x_root,event.y_root)
                return
        popup_menu=Menu(self.canvas1,tearoff=0)
        popup_menu.add_command(label="Switch Properties",command=self.switchdetails)
        popup_menu.post(event.x_root,event.y_root)

    def popup_legacyswitch(self,event):
        item=event.widget
        self.selectedNode=event.widget
        for bouton in self.list_buttons.values():
            etat_bouton =str(bouton['state'])
            if etat_bouton == 'disabled':
                popup_menu=Menu(self.canvas1,tearoff=0)
                popup_menu.add_command(label="List Bridge",command=self.listBridge)
                popup_menu.post(event.x_root,event.y_root)
                return

    def popup_legacyrouter(self,event):
        item=event.widget
        self.selectedNode=event.widget
        for bouton in self.list_buttons.values():
            etat_bouton =str(bouton['state'])
            if etat_bouton == 'disabled':
                popup_menu=Menu(self.canvas1,tearoff=0)
                popup_menu.add_command(label="Terminal",command=self.xterm)
                popup_menu.post(event.x_root,event.y_root)
                return

    def popup_link(self,event):
        for bouton in self.list_buttons.values():
            etat_bouton =str(bouton['state'])
            #print("etat bouton" + etat_bouton)
            if etat_bouton == 'disabled':
                popup_menu=Menu(self.canvas1,tearoff=0)
                popup_menu.add_command(label="Link down",command=self.linkDown)
                popup_menu.add_command(label="Link Up",command=self.linkUp)
                popup_menu.post(event.x_root,event.y_root)
                return
        popup_menu=Menu(self.canvas1,tearoff=0)
        popup_menu.add_command(label="Link Properties",command=self.linkdetails)
        popup_menu.post(event.x_root,event.y_root)

    def listBridge( self, _ignore=None ):
        selectedNode=self.selectedNode  #widget
        itemNode=self.widgetToItem[selectedNode]
        name=self.itemToName[itemNode]
        tags = self.canvas1.gettags(itemNode)

        if name not in self.net.nameToNode:
            return
        if 'Switch' in tags or 'LegacySwitch' in tags:
            call(["xterm -T 'Bridge Details' -sb -sl 2000 -e 'ovs-vsctl list bridge " + name + "; read -p \"Press Enter to close\"' &"], shell=True)

    @staticmethod
    def ovsShow(_ignore=None):
        call(["xterm -T 'OVS Summary' -sb -sl 2000 -e 'ovs-vsctl show; read -p \"Press Enter to close\"' &"],shell=True)


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


    #Placer un bouton sur le canevas
    def canvasHandle(self,event):
        x1=event.x
        y1=event.y
        if (self.activeButton == 'Switch'):
            self.switchNumber+=1
            name_switch='s'+str(self.switchNumber) #s1
            #bouton1=Button(self.canvas,image=self.images['Switch'],text=name_switch,compound='top',bg='white')
            bouton1=Button(self.canvas1,image=self.images['Switch'],text=name_switch,compound='top',bg='white')
            self.switchOptions[bouton1]={}
            self.switchOptions[bouton1]['numSwitch']=self.switchNumber
            self.switchOptions[bouton1]['nameSwitch']=name_switch
            #self.switchOptions[bouton1]['controllers']=[]
            #self.switchOptions[bouton1]['options']={"controllers": [],"hostname": name_switch,"nodenum":self.switchNumber,"switchType":"Default",'stopCommand':'','sflow':0,'switchIP':'','dpid':'','dpctl':'','startCommand':'','netflow':0,'externalInterfaces':[]}
            self.switchOptions[bouton1]['options']={"controllers": [],"hostname": name_switch,"nodeNum":self.switchNumber,"switchType":"Default"}
            self.name_switch.append(name_switch)
            #id1=self.canvas.create_window((x1,y1),anchor='center',window=bouton1,tags='Switch')
            id1=self.canvas1.create_window((x1,y1),anchor='center',window=bouton1,tags='Switch')
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
            #bouton2=Button(self.canvas,image=self.images['Host'],text=name_host,bg='white',compound='top')
            bouton2=Button(self.canvas1,image=self.images['Host'],text=name_host,bg='white',compound='top')
            self.hostOptions[bouton2]={}
            #self.hostOptions[bouton2]['sched']='host'
            self.hostOptions[bouton2]['numhost']=self.hostNumber
            self.hostOptions[bouton2]['hostname']=name_host
            self.hostOptions[bouton2]['options']={}
            #self.hostOptions[bouton2]['options']={'hostname':name_host,"nodeNum":self.hostNumber,"sched":"host",'stopCommand':'','externalInterfaces':[],'ip':'','privateDirectory':[],'nodeNum':self.hostNumber,'vlanInterfaces':[],'cores':'','startCommand':'','cpu':'','defaultRoute':''}
            #id2=self.canvas.create_window((x1,y1),anchor='center',window=bouton2,tags='host')
            self.hostOptions[bouton2]['options']={'hostname':name_host,"nodeNum":self.hostNumber,"sched":"host"}
            id2=self.canvas1.create_window((x1,y1),anchor='center',window=bouton2,tags='host')
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
            #bouton3=Button(self.canvas,image=self.images['Controller'],bg='white',text=name_controller,compound='top')
            bouton3=Button(self.canvas1,image=self.images['Controller'],bg='white',text=name_controller,compound='top')
            id3=self.canvas1.create_window((x1,y1),anchor='center',window=bouton3,tags='Controller')
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
            bouton4=Button(self.canvas1,image=self.images['LegacySwitch'],text=name_legacySwitch,bg='white',compound='top')
            self.buttons_canevas[name_legacySwitch]=bouton4
            self.legacySwitchOptions[bouton4]={}
            self.legacySwitchOptions[bouton4]['name']=name_legacySwitch
            self.legacySwitchOptions[bouton4]['number']=self.switchNumber
            self.legacySwitchOptions[bouton4]['options']={'num':self.switchNumber,'hostname':name_legacySwitch,'switchType':'LegacySwitch'}
            id4=self.canvas1.create_window((x1,y1),anchor='center',window=bouton4,tags='LegacySwitch')
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
            bouton5=Button(self.canvas1,image=self.images['LegacyRouter'],text=name_legacyRouter,bg='white',compound='top')
            self.buttons_canevas[name_legacyRouter]=bouton5
            self.legacyRouterOptions[bouton5]={}
            self.legacyRouterOptions[bouton5]['name']=name_legacyRouter
            self.legacyRouterOptions[bouton5]['number']=self.switchNumber
            self.legacyRouterOptions[bouton5]['options']={'num':self.switchNumber,'hostname':name_legacyRouter,'switchType':'LegacyRouter'}
            id5=self.canvas1.create_window((x1,y1),anchor='center',window=bouton5,tags='LegacyRouter')
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
            tag = self.canvas1.gettags(item)
            x,y = self.canvas1.coords(item)
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
                icon = Button(self.canvas1,image=self.images['Host'])
                item = self.canvas1.create_window(x,y,anchor='c',window=icon,tags='host')
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
                icon2=Button(self.canvas1,image=self.images['Controller'])
                item2=self.canvas1.create_window(x2,y2,anchor='c',window=icon2,tags='Controller')
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
                    icon1 = Button(self.canvas1,image=self.images['Switch'])
                    item1=self.canvas1.create_window(x1,y1,anchor='c',window=icon1,tags='Switch')
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
                            dx, dy = self.canvas1.coords(controller_item)
                            self.link = self.canvas1.create_line(float(x1),float(y1),dx,dy,width=4,fill='red',dash=(6, 4, 2, 4),tag='link')
                            self.canvas.itemconfig(self.link,tags=self.canvas1.gettags(self.link)+('control',))
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
                    icon3=Button(self.canvas1,image=self.images['LegacySwitch'])
                    item3=self.canvas1.create_window(x3,y3,anchor='c',window=icon3,tags='LegacySwitch')
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
                    icon4=Button(self.canvas1,image=self.images['LegacyRouter'])
                    item4=self.canvas1.create_window(x4,y4,anchor='c',window=icon4,tags='LegacyRouter')
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
                 srcx,srcy=self.canvas1.coords(self.nameToItem[src]); #coordonnées de la source
                 destx,desty=self.canvas1.coords(self.nameToItem[dst]);
                 self.link=self.canvas1.create_line(srcx,srcy,destx,desty,width=4,fill='blue',tag='link')
                 self.canvas1.itemconfig(self.link,tags=self.canvas1.gettags(self.link)+('data',))
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
        return self.canvas1.canvasx( x_root ) - self.canvas1.winfo_rootx()

    def canvasy( self, y_root ):
        return self.canvas1.canvasy( y_root ) - self.canvas1.winfo_rooty()

    def findObject(self,x,y):
        items = self.canvas1.find_overlapping(x,y,x,y)
        if len(items) == 0:
            return
        else:
            return items[0]

    def createLink(self,event):
        w = event.widget
        item = self.widgetToItem[w]
        x, y = self.canvas1.coords(item)
        self.coordonnees["i0"]=x
        self.coordonnees["j0"]=y
        self.link = self.canvas1.create_line(x,y,x,y,width=4,fill='blue',tag='link')
        self.links[self.link]={}
        tags = self.canvas1.gettags(item)
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
            self.canvas1.itemconfig(link,fill='red')

        def linkColorLeave(_event,link=self.link):
            self.canvas1.itemconfig(link,fill='blue')

        self.canvas1.tag_bind(self.link,'<Enter>',linkColorEntry)
        self.canvas1.tag_bind(self.link,'<Leave>',linkColorLeave)
        self.canvas1.tag_bind(self.link,'<Button-3>',self.popup_link)


    def dragLink(self,event):
        b = self.canvasx( event.x_root ) # coordonnées d'arrivée
        n = self.canvasy( event.y_root ) # coordonnées d'arrivée
        self.canvas1.coords(self.link,self.coordonnees["i0"],self.coordonnees["j0"],b,n)

    def ControlLinkBindings( self ):

        def linkColorEntry1(_event,link=self.link ):
            self.selectedLink=link
            self.canvas1.itemconfig(link,fill='blue')

        def linkColorLeave1( _event,link=self.link):
            self.canvas1.itemconfig( link, fill='red' )

        self.canvas1.tag_bind(self.link,'<Enter>',linkColorEntry1)
        self.canvas1.tag_bind(self.link,'<Leave>',linkColorLeave1)

    def linkUp(self):
        link = self.selectedLink
        src = self.links[link]['src']
        dst = self.links[link]['dest']
        self.net.configLinkStatus(src,dst,'up')
        self.canvas1.itemconfig(link, dash=())

    def linkDown(self):
        link = self.selectedLink
        src = self.links[link]['src']
        dst = self.links[link]['dest']
        self.net.configLinkStatus(src,dst,'down')
        self.canvas1.itemconfig(link, dash=())

    def finishLink(self,event):
        #we drag from the widget , we use root coordonnees
        src = self.linkWidget
        srcItem=self.widgetToItem[src]
        x = self.canvasx(event.x_root) # coordonnées d'arrivée du lien
        y= self.canvasy(event.y_root) # coordonnées d'arrivée du lien
        target = self.findObject(x,y) # item du widget d'arrivée
        srctags=self.canvas1.gettags(srcItem)
        desttags=self.canvas1.gettags(target)
        dest1=self.itemToWidget.get(target,None) #widget correspondant à l'item se trouvant à l'arrivée

        if(dest1 == None):
            self.canvas1.delete( self.link )
            del self.source[src]
            del self.links[self.link]
            return
            #self.link=None
            #self.linkWidget=None

        if (dest1 != None):
            tags=self.canvas1.gettags(target)
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
              self.canvas1.delete(self.link)
              del self.links[self.link]
              return
              #self.link=None
              #self.linkWidget=None
        elif(('Controller' in srctags and 'Switch' in desttags)or
            ('Switch' in srctags and 'Controller' in desttags)):
            linkType='control'
            self.links[self.link]['type']='control'
            self.canvas1.itemconfig(self.link,dash=(6, 4, 2, 4),fill='red')
            self.ControlLinkBindings()
            self.canvas1.itemconfig(self.link,tags=self.canvas1.gettags(self.link)+(linkType,))
            self.liens.append(self.link)
        else:
            #print("i m not a controller , setting links")
            linkType='data'
            self.links[self.link]['type']='data'
            self.DataLinkBindings()
            self.canvas1.itemconfig(self.link,tags=self.canvas1.gettags(self.link)+(linkType,))
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
        self.textCanvas.tag_configure('big',justify='center',font=('Helvetica',16,'bold'),foreground='RoyalBlue1',underline=1)
        self.textCanvas.tag_configure('color',font=('Helvetica',11,'bold'))
        self.textCanvas.config(state="normal")
        self.textCanvas.delete('1.0',END)
        self.textCanvas.insert(END,'\nLinks between nodes\n\n','big')
        for node in nodes:
            self.textCanvas.insert(INSERT,str(node.name)+' ','color')
            for intf in node.intfList():
                self.textCanvas.insert(INSERT,str(intf)+':','color')
                if intf.link:
                    intfs = [ intf.link.intf1, intf.link.intf2 ]
                    intfs.remove( intf )
                    self.textCanvas.insert(INSERT,intfs[0],'color')
                    self.textCanvas.insert(INSERT,' ','color')
                else:
                    self.textCanvas.insert(INSERT,' ','color')
            self.textCanvas.insert(INSERT,'\n')
        self.textCanvas.config(state='disabled')

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
                tags = self.canvas1.gettags(item)
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
            tags = self.canvas1.gettags(item)

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
                tags = self.canvas1.gettags(item1)

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
                tags = self.canvas1.gettags(item2)

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

    def stop_net( self ):
        if self.net is not None:
            for widget in self.widgetToItem:
                item=self.widgetToItem[widget]
                name = self.itemToName[item]
                tags = self.canvas1.gettags(item)
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
            tags = self.canvas1.gettags(item)
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
            tags = self.canvas1.gettags(link)
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
