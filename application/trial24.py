from tkinter import *
from PIL import Image,ImageTk
from tkinter import ttk
import logging
from tkinter import filedialog as tkFileDialog
#from mininet.util import netParse,ipAdd
from functools import partial
logging.basicConfig(level=logging.INFO)
import os
import json


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
        self.preferences={"dpctl": "","ipBase": "10.0.0.0/8","netflow": {"nflowAddId": "0","nflowTarget": "","nflowTimeout": "600"},"openFlowVersions": {"ovsOf10": "1","ovsOf11": "0","ovsOf12": "0","ovsOf13": "0"},"sflow" : {"sflowHeader": "128","sflowPolling": "30","sflowSampling": "400","sflowTarget": ""},"startCLI": "0","switchType": "ovs","terminalType": "xterm"}
        self.list_buttons={}
        self.buttons_canevas={}
        self.links={}
        self.itemToName={}
        self.liens=[]
        self.switchOptions={}
        self.hostOptions={}
        self.controllerOptions={}
        self.coordonnees={"i0":0,"j0":0,"i1":0,"j1":0}
        self.create_menu_bar(window)
        self.widgetToItem={}
        self.itemToWidget={}
        self.source={}
        self.nameToItem={}
        self.net=None
        #self.dest={}
        self.canvas=self.create_canvas(window)
        self.elements=['Switch','Host','Link','LegacyRouter','LegacySwitch','Controller']
        self.nodePref = {'Switch':'s','Host':'h','LegacyRouter':'r','LegacySwitch':'s','Controller':'c'}
        self.images=self.netImages()
        self.create_buttons(window)
        #self.make_draggable()
        #self.movable_buttons()
        #self.addNodeToCanvas('Switch',50,50)

    def create_menu_bar(self,window):
        mainmenu = Menu(window)

        sousmenu1=Menu(mainmenu,tearoff=0)
        sousmenu1.add_command(label="New",command=self.nvTopology)
        sousmenu1.add_command(label="Open",command=self.loadTopology)
        sousmenu1.add_command(label="Save",command=self.saveTopology)
        sousmenu1.add_command(label="Export level 2 script")
        sousmenu1.add_command(label="Quit")
        mainmenu.add_cascade(label="File",menu=sousmenu1)

        sousmenu2=Menu(mainmenu,tearoff=0)
        sousmenu2.add_command(label="Cut")
        sousmenu2.add_command(label="Preferences",command=self.setPreferences)
        mainmenu.add_cascade(label='Edit',menu=sousmenu2)

        sousmenu3=Menu(mainmenu,tearoff=0)
        sousmenu3.add_command(label="Run")
        sousmenu3.add_command(label="Stop")
        sousmenu3.add_command(label="Show OVS Summary")
        sousmenu3.add_command(label="Root Terminal",command=self.display_shell)
        mainmenu.add_cascade(label='Run',menu=sousmenu3)

        sousmenu4=Menu(mainmenu,tearoff=0)
        sousmenu4.add_command(label="About NetView")
        mainmenu.add_cascade(label='Help',menu=sousmenu4)

        window.config(menu=mainmenu)


    def create_canvas(self,window):
        #canvas = Canvas(window,width='1000',height='1000',bg='pink')
        canvas = Canvas(window,width='1500',height='1500',bg='pink')
        canvas.place(x='100',y='0')
        canvas.bind('<ButtonPress-1>',self.canvasHandle)
        #canvas.bind('<B1-Motion>',self.dragCanevas)
        #canvas.bind('<ButtonRelease-1>',self.dropCanevas)
        return canvas

    def create_buttons(self,window):
        abs=0;
        ord=0;
        for n in self.elements :
            cmd=(lambda t=n:self.activate_widget(t))
            self.list_buttons[n]=Button(window) #switch , cursor , host
            self.list_buttons[n].config(relief="raised")
            self.list_buttons[n].config(image=self.images[n],command=cmd)
            self.list_buttons[n].place(x=str(abs),y=str(ord))
            ord+=90
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
        #print("buttons_canevas:"+str(self.buttons_canevas))
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
        self.controllerOptions={}
        self.itemToName={}

    def selectItem(self,item):
        self.lastSelection=self.selection
        self.currentSelection=item

    #Ajoute un noeud dans le canvas à une position donnée , don't forget links
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

    def make_draggable_legacyRouter(self,widget):
        widget.bind("<Button-1>", self.click)
        widget.bind("<B1-Motion>", self.drag)
        widget.bind("<ButtonRelease-1>",self.release)


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
            self.finishLink(event)

    def on_drag_start(self,event):
        widget = event.widget
        widget._drag_start_x = event.x
        widget._drag_start_y = event.y

    def on_drag_motion(self,event):
        widget = event.widget
        item=self.widgetToItem[widget]
        x1,y1=self.canvas.coords(item)
        x = widget.winfo_x() - widget._drag_start_x + event.x #coordonnées d'arrivée
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
        popup_menu=Menu(self.canvas,tearoff=0)
        #popup_menu.add_command(label="Delete",command=item.destroy())
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
        popup_menu=Menu(self.canvas,tearoff=0)
        popup_menu.add_command(label="Switch Properties",command=self.switchProperties)
        popup_menu.post(event.x_root,event.y_root)

    def popup_link(self,event):
        popup_menu=Menu(self.canvas,tearoff=0)
        popup_menu.add_command(label="Link Properties",command=self.linkProperties)
        popup_menu.post(event.x_root,event.y_root)

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

    def logInformationsHost(self):
        newhostoptions={}
        newhostoptions['nodeNum']=self.hostOptions[self.selectedNode]['numhost']
        newhostoptions['hostname']=hostEntries['hostname'].get()
        newhostoptions['ip']=hostEntries['ipAddress'].get()
        newhostoptions['defaultRoute']=hostEntries['defaultRoute'].get()
        newhostoptions['cores']=hostEntries['cores'].get()
        newhostoptions['startCommand']=hostEntries['start'].get()
        newhostoptions['stopCommand']=hostEntries['stop'].get()
        newhostoptions['sched']=hostEntries['sched']
        newhostoptions['externalInterfaces']=externalEntries
        newhostoptions['privateDirectory']=directoryEntries
        newhostoptions['vlanInterfaces']=vlanEntries
        self.hostOptions[self.selectedNode]['options']=newhostoptions
        logging.info('New host details for ' + newhostoptions['hostname'] + '=' + str(newhostoptions) + '\n')

    def logInformationsController(self):
        newcontrolleroptions={}
        newcontrolleroptions['hostname']=self.controllerOptions[self.selectedNode]['hostname']
        newcontrolleroptions['remotePort']=listProperties['remotePort'].get()
        newcontrolleroptions['remoteIP']=listProperties['remoteIP'].get()
        newcontrolleroptions['controllerType']=listProperties['controllerType']
        newcontrolleroptions['controllerProtocol']=listProperties['controllerProtocol']
        self.controllerOptions[self.selectedNode]['options']=newcontrolleroptions
        logging.info('New controller details for' + newcontrolleroptions['hostname'] + '=' + str(newcontrolleroptions) + '\n')

    def changeControllerType(self,*args):
        listProperties['controllerType']=var25.get()

    def changeProtocol(self,*args):
        listProperties['controllerProtocol']=var26.get()

    def controllerProperties(self):
        root=Toplevel()
        root.geometry('300x320')
        global listProperties
        listProperties={}
        listProperties['type']=None
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
        optionsProtocol=['TCP','SSL']

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
        newLinkOptions={}
        newLinkOptions['loss']=linkEntries['loss'].get()
        newLinkOptions['jitter']=linkEntries['jitter'].get()
        newLinkOptions['speedup']=linkEntries['speedup'].get()
        newLinkOptions['delay']=linkEntries['delay'].get()
        newLinkOptions['bw']=linkEntries['bw'].get()
        newLinkOptions['max_queue_size']=linkEntries['max_queue_size'].get()
        self.links[self.selectedLink]['options']=newLinkOptions
        logging.info('New link details for ' + '=' + str(newLinkOptions) + '\n')

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
        listVariable["controllers"]=self.switchOptions[self.selectedNode]["controllers"] #controllers

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
        logging.info('New switch details for ' + str(newSwitchOptions['hostname']) + '=' + str(newSwitchOptions) + '\n')

    def logInformationsPreferences(self):
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
        newPrefOptions['netflow']['nFlowTarget']=variables['nFlowTarget'].get()
        newPrefOptions['netflow']['nFlowTimeout']=variables['nFlowTimeout'].get()
        newPrefOptions['netflow']['nFlowAddId']=nFlowAddId.get()
        newPrefOptions['startCLI']=varStartCLI.get()
        self.preferences=newPrefOptions
        logging.info('New Prefs ' + '=' + str(newPrefOptions) + '\n')

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
        varStartCLI=StringVar()
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
        var_2=StringVar()
        var_2.set("400")
        entry_4=Entry(frame2,textvariable=var_2)
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

    #def logInformationsPreferences(self):

    #Placer un bouton sur le canevas
    def canvasHandle(self,event):
        x1=event.x
        y1=event.y
        if (self.activeButton == 'Switch'):
            bouton1=Button(self.canvas,image=self.images['Switch'])
            self.switchNumber+=1
            name_switch='s'+str(self.switchNumber) #s1
            self.switchOptions[bouton1]={}
            self.switchOptions[bouton1]['numSwitch']=self.switchNumber
            self.switchOptions[bouton1]['nameSwitch']=name_switch
            self.switchOptions[bouton1]['controllers']=[]
            self.switchOptions[bouton1]['options']={"controllers": [],"hostname": name_switch,"nodenum":self.switchNumber,"switchType":"default"}
            id1=self.canvas.create_window((x1,y1),anchor='center',window=bouton1,tags='Switch')
            self.widgetToItem[bouton1]=id1
            self.itemToWidget[id1]=bouton1
            self.itemToName[id1]=name_switch
            self.buttons_canevas[name_switch]=bouton1
            self.make_draggable_switch(self.buttons_canevas[name_switch])
            self.nb_widget_canevas+=1
            self.list_buttons['Switch'].config(relief="raised")
            self.activeButton=None
        elif(self.activeButton == 'Host'):
            bouton2=Button(self.canvas,image=self.images['Host'])
            self.hostNumber+=1
            name_host='h'+str(self.hostNumber) #h1
            self.hostOptions[bouton2]={}
            #self.hostOptions[bouton2]['sched']='host'
            self.hostOptions[bouton2]['numhost']=self.hostNumber
            self.hostOptions[bouton2]['hostname']=name_host
            self.hostOptions[bouton2]['options']={}
            self.hostOptions[bouton2]['options']={'hostname':name_host,"nodeNum":self.hostNumber,"sched":"host"}
            id2=self.canvas.create_window((x1,y1),anchor='center',window=bouton2,tags='host')
            self.itemToName[id2]=name_host
            self.widgetToItem[bouton2]=id2
            self.itemToWidget[id2]=bouton2
            self.buttons_canevas[name_host]=bouton2
            self.make_draggable_host(self.buttons_canevas[name_host])
            self.nb_widget_canevas+=1
            self.list_buttons['Host'].config(relief="raised")
            self.activeButton=None
        elif(self.activeButton == 'Controller'):
            bouton3=Button(self.canvas,image=self.images['Controller'])
            self.controllerNumber+=1
            name_controller='c'+str(self.controllerNumber)
            id3=self.canvas.create_window((x1,y1),anchor='center',window=bouton3,tags='Controller')
            self.controllerOptions[bouton3]={}
            self.controllerOptions[bouton3]['numController']=self.controllerNumber
            self.controllerOptions[bouton3]['hostname']=name_controller
            self.controllerOptions[bouton3]['options']={'hostname':name_controller,'remotePort':6633,'controllerType':'OpenFlow Reference','controllerProtocol':'TCP','remoteIP':'127.0.0.1'}
            self.widgetToItem[bouton3]=id3
            self.itemToWidget[id3]=bouton3
            self.itemToName[id3]=name_controller
            self.buttons_canevas[name_controller]=bouton3
            self.make_draggable_controller(self.buttons_canevas[name_controller])
            self.nb_widget_canevas+=1
            self.list_buttons['Controller'].config(relief="raised")
            self.activeButton=None
        elif(self.activeButton == 'LegacySwitch'):
            bouton4=Button(self.canvas,image=self.images['LegacySwitch'])
            id4=self.canvas.create_window((x1,y1),anchor='center',window=bouton4,tags='LegacySwitch')
            self.widgetToItem[bouton4]=id4
            self.itemToWidget[id4]=bouton4
            self.make_draggable_legacySwitch(bouton4)
            self.nb_widget_canevas+=1
            self.list_buttons['LegacySwitch'].config(relief='raised')
            self.activeButton=None
        elif(self.activeButton == 'LegacyRouter'):
            bouton5=Button(self.canvas,image=self.images['LegacyRouter'])
            id5=self.canvas.create_window((x1,y1),anchor='center',window=bouton5,tags='LegacyRouter')
            self.widgetToItem[bouton5]=id5
            self.itemToWidget[id5]=bouton5
            self.make_draggable_legacyRouter(bouton5)
            self.nb_widget_canevas+=1
            self.list_buttons['LegacySwitch'].config(relief='raised')
            self.activeButton=None

    def saveTopology(self):
        fileTypes = [("Mininet Topology","*.mn"),("All Files",'*')]
        result = tkFileDialog.asksaveasfilename(filetypes=fileTypes,title="Save topology")
        savingSwitches=[]
        savinghosts=[]
        savinglinks=[]
        dictionary={}
        for item in self.widgetToItem.values():
            tag = self.canvas.gettags(item)
            x,y = self.canvas.coords(item)
            widget=self.itemToWidget[item]
            if('Switch' in tag):
                switchNum=self.switchOptions[widget]['numSwitch']
                #print('switchnum'+str(switchNum))
                switchName=self.switchOptions[widget]['nameSwitch']
                savingSwitch={'number':str(switchNum),'x':str(x),'y':str(y),'opts':self.switchOptions[widget]['options']}
                #print('switchoptions:'+str(savingSwitch['opts']))
                savingSwitches.append(savingSwitch)
            elif('host' in tag):
                hostNum=self.hostOptions[widget]['numhost']
                savinghost={'number':str(hostNum),'x':str(x),'y':str(y),'opts':self.hostOptions[widget]['options']}
                #print('hostnum'+str(savinghost['number']))
                #print('hostoptions:'+str(savinghost['opts']))
                savinghosts.append(savinghost)
        dictionary['hosts']=savinghosts
        dictionary['switches']=savingSwitches
        dictionary['application']=self.preferences

        for link in self.links.keys():
            options={}
            src = self.links[link]['src']
            target = self.links[link]['dest']
            options=self.links[link]['options']
            savingLink={'src':src,'dest':target,'options':options}
            savinglinks.append(savingLink)

        dictionary['links']=savinglinks
        dictionary['application']=self.preferences

        f = open(result,'w')
        f.write(json.dumps(dictionary, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()

    def loadTopology(self):
        fileTypes = [("Mininet Topology","*.mn"),("All Files",'*')]
        f=tkFileDialog.askopenfile(filetypes=fileTypes,title="Open file",mode='r')
        self.nvTopology()
        topologyLoaded=json.load(f)
        print('\n')
        print(topologyLoaded)

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
                print(icon)
                print('\n')
                item = self.canvas.create_window(x,y,anchor='c',window=icon,tags='host')
                self.widgetToItem[icon]=item
                self.itemToWidget[item]=icon
                self.nameToItem[hostname]=item;
                self.make_draggable_host(icon)
                self.buttons_canevas[hostname]=icon
                self.hostOptions[icon]={}
                self.hostOptions[icon]['numhost']=self.hostNumber
                self.hostOptions[icon]['hostname']=hostname
                self.hostOptions[icon]['options']=hosts[i]['opts']

        #load switches
        switches=topologyLoaded['switches']
        if(len(switches)!=0):
            for i in range(0,len(switches)):
                switchNum=switches[i]['number']
                switchName='s'+str(switchNum)
                x1=switches[i]['x']
                y1=switches[i]['y']
                self.switchNumber+=1
                icon1 = Button(self.canvas,image=self.images['Switch'])
                print('\n')
                print(icon1)
                item1=self.canvas.create_window(x1,y1,anchor='c',window=icon1,tags='Switch')
                self.widgetToItem[icon1]=item1
                self.itemToWidget[item1]=icon1
                self.make_draggable_switch(icon1)
                self.buttons_canevas[switchName]=icon1
                self.nameToItem[switchName]=item1;
                self.switchOptions[icon1]={}
                self.switchOptions[icon1]['numSwitch']=switchNum
                self.switchOptions[icon1]['nameSwitch']=switchName
                self.switchOptions[icon1]['options']=switches[i]['opts']

        #load Links
        links=topologyLoaded['links']
        if(len(links)!=0):
             for i in range(0,len(links)):
                 src = links[i]['src'] #nom de SRC
                 dest=links[i]['dest'] #nom de DEST
                 srcx,srcy=self.canvas.coords(self.nameToItem[src]); #coordonnées de la source
                 destx,desty=self.canvas.coords(self.nameToItem[dest]);

                 self.link=self.canvas.create_line(srcx,srcy,destx,desty,width=4,fill='blue',tag='link')
                 self.links[self.link]={}
                 self.links[self.link]['src']=src
                 self.links[self.link]['dest']=dest
                 self.links[self.link]['options']=links[i]['options']
                 self.DataLinkBindings()
                 self.link=None
                 self.linkWidget=None

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
        self.links[self.link]['options']={}
        self.liens.append(self.link)
        self.DataLinkBindings()
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
        if (dest1 != None):
            tags=self.canvas.gettags(target)
            if('Switch' in tags):
                self.links[self.link]['dest']=self.switchOptions[dest1]['nameSwitch']
            elif('host' in tags):
                self.links[self.link]['dest']=self.hostOptions[dest1]['hostname']
            elif('host' in tags):
                self.links[self.link]['dest']=self.controllerOptions[dest1]['hostname']
        if(dest1 == None):
            self.canvas.delete( self.link )
            del self.source[src]
            self.link=None
            self.linkWidget=None
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
              self.link=None
              self.linkWidget=None

        # Set link type
        linkType='data'
        if (('Controller' in srctags and 'Switch' in desttags)or
            ('Switch' in srctags and 'Controller' in desttags)):
            linkType='control'
            self.canvas.itemconfig(self.link,dash=(6, 4, 2, 4),fill='red')
            self.ControlLinkBindings()
        self.link=None
        self.linkWidget=None

    def build():
        dpctl = None
        if len(self.preferences['dpctl'])!=0:
            dpctl = int(self.preferences['dpctl'])
        net = Mininet(topo=None,listenPort=dpctl,build=False,ipBase=self.preferences['ipBase'] )

        self.buildNodes(net)
        net.build()
        return net

    def buildNodes(self,net):
        logging.info("Getting Hosts and Switches.\n")
        for item in self.widgetToItem.values():
            tags = self.canvas.gettags(item)
            name=self.itemToName[item]

            if 'Switch' in tags:
                options = self.switchOptions[self.itemToWidget[item]]
                switch_options=options['options']
                print("switch_options:"+ str(switch_options))

                # Create switch class
                switchClass = customOvs
                switch_properties={}
                if 'dpctl' in switch_options:
                    switch_properties['listenPort']=int(switch_options['dpctl'])
                if 'dpid' in opts:
                    switch_properties['dpid']=switch_options['dpid']
                if switch_options['switchType'] == 'default':
                    if self.preferences['switchType'] == 'Indigo Virtual Switch':
                        switchClass = IVSSwitch
                    elif self.preferences['switchType'] == 'Userspace Switch':
                        switchClass = CustomUserSwitch
                    elif self.preferences['switchType'] == 'Userspace Switch inNamespace':
                        switch_properties['inNamespace'] = True
                        switchClass = CustomUserSwitch
                    else:
                        switchClass = customOvs
                elif switch_options['switchType'] == 'Userspace Switch':
                    switchClass = CustomUserSwitch
                elif switch_options['switchType'] == 'Underspace Switch inNamespace':
                    switchClass = CustomUserSwitch
                    switch_properties['inNamespace'] = True
                elif switch_options['switchType'] == 'Indigo Virtual Switch':
                    switchClass = IVSSwitch
                else:
                    switchClass = customOvs

                if switchClass == customOvs:
                    # Set OpenFlow versions
                    self.openFlowVersions = []
                    if self.preferences['openFlowVersions']['ovsOf10'] == '1':
                        self.openFlowVersions.append('OpenFlow10')
                    if self.preferences['openFlowVersions']['ovsOf11'] == '1':
                        self.openFlowVersions.append('OpenFlow11')
                    if self.preferences['openFlowVersions']['ovsOf12'] == '1':
                        self.openFlowVersions.append('OpenFlow12')
                    if self.preferences['openFlowVersions']['ovsOf13'] == '1':
                        self.openFlowVersions.append('OpenFlow13')
                    protocolList = ",".join(self.openFlowVersions)
                    switch_properties['protocols'] = protocolList
                newSwitch = net.addSwitch(name,cls=switchClass,**switch_properties)
                print("newswitch:"+newswitch)

            elif 'LegacySwitch' in tags:
                newSwitch = net.addSwitch(name,cls=LegacySwitch)
            elif 'LegacyRouter' in tags:
                newSwitch = net.addHost(name,cls=LegacyRouter)
            elif 'Host' in tags:
                options = self.hostOptions[self.itemToWidget[item]]
                host_options=options['options']
                ip = None
                defaultRoute = None
                if('defaultRoute' in host_options and len(host_options['defaultRoute'])>0):
                    defaultRoute='via' + host_options['defaultRoute']
                if ('ip' in host_options and len(host_options['ip'])>0):
                    ip = host_options['ip']
                else:
                    nodeNum = self.hostOptions[self.itemToWidget[item]]['nodeNum']
                    ipBaseNum, prefixLen=netParse(self.preferences['ipBase'])
                    ip=ipAdd(i=nodeNum, prefixLen=prefixLen, ipBaseNum=ipBaseNum)

                # Create correct host class
                if 'cores' in host_options or 'cpu' in host_options:
                    if 'privateDirectory' in host_options:
                        hostCls=partial(CPULimitedHost,privateDirs=host_options['privateDirectory'] )
                    else:
                        hostCls=CPULimitedHost
                else:
                    if 'privateDirectory' in host_options:
                        hostCls=partial(Host,privateDirs=host_options['privateDirectory'])
                    else:
                        hostCls=Host
                debug( hostCls,'\n')
                newHost = net.addHost(name,cls=hostCls,ip=ip,defaultRoute=defaultRoute)

            elif 'Controller' in tags:
                options = self.controllerOptions[self.itemToWidget[item]]
                controller_options = options['options']

                controllerType = controller_options['controllerType']
                if 'controllerProtocol' in controller_options:
                    controllerProtocol = controller_options['controllerProtocol']
                else :
                    controllerProtocol = 'TCP'
                    controller_options['controllerProtocol'] = 'TCP'
                controllerIP = controller_options['remoteIP']
                controllerPort = controller_options['remotePort']

                logging.info('Getting controller selection:' + controllerType,'\n')
                if controllerType == 'Remote Controller':
                    net.addController(name=name,controller=RemoteController,ip=controllerIP,protocol=controllerProtocol,port=controllerPort)
                elif controllerType == 'In-Band Controller':
                    net.addController(name=name,controller=InbandController,ip=controllerIP,protocol=controllerProtocol,port=controllerPort)
                elif controllerType == 'OVS Controller':
                    net.addController(name=name,controller=OVSController,protocol=controllerProtocol,port=controllerPort)
                else:
                    net.addController(name=name,controller=Controller,protocol=controllerProtocol,port=controllerPort)
            else:
                raise Exception( "Cannot create mystery node: " + name )

    def netImages(self):
        img1=PhotoImage(file="ressources/switch.gif")
        img2=PhotoImage(file="ressources/controleur.png")
        img3=PhotoImage(file="ressources/host.png")
        img4=PhotoImage(file="ressources/line.png")
        img5=PhotoImage(file="ressources/legacyRouter.png")
        img6=PhotoImage(file="ressources/legacyswitch.png")
        img1_mini=img1.subsample(7,8)
        img2_mini=img2.subsample(3,4)
        img3_mini=img3.subsample(4,4)
        img4_mini=img4.subsample(4,4)
        img5_mini=img5.subsample(11,8)
        img6_mini=img6.subsample(3,3)
        dict_images={'Switch': img1_mini,'Controller':img2_mini,'Host':img3_mini,'Link':img4_mini,'LegacyRouter':img5_mini,'LegacySwitch':img6_mini}
        return dict_images


def main():
    fenetre= Tk()
    fenetre.title('New Miniedit')
    fenetre['bg']="white"
    fenetre.geometry("1000x1000+350+400")

    interface = Interface(fenetre)
    fenetre.mainloop()

if __name__ == '__main__':
    main()
