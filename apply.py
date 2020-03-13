from tkinter import *
from PIL import Image,ImageTk
from tkinter import ttk


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
        self.nb_widget_canevas=0
        self.list_buttons={}
        self.buttons_canevas={}
        self.links={}
        self.Source_Target={}
        self.coordonnees={"i0":0,"j0":0,"i1":0,"j1":0}
        self.create_menu_bar(window)
        self.widgetToItem={}
        self.itemToWidget={}
        self.source={}
        self.dest={}
        self.canvas=self.create_canvas(window)
        self.elements=['Switch','Cursor','Host','Link']
        self.images=self.netImages()
        self.create_buttons(window)
        #self.make_draggable()
        #self.movable_buttons()
        #self.addNodeToCanvas('Switch',50,50)

    def create_menu_bar(self,window):
        menu = Menu(window)
        sousmenu=Menu(menu,tearoff=0)
        menu.add_cascade(label='Topology',menu=sousmenu)
        sousmenu.add_command(label="New topology")
        sousmenu.add_command(label="Save topology")
        window.config(menu=menu)

    def create_canvas(self,window):
        canvas = Canvas(window,width='1000',height='1000',bg='pink')
        canvas.place(x='80',y='0')
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
            ord+=100
        #print(self.list_buttons)

#activate a widget in the toolbar
    def activate_widget(self,nodeName):
        if self.activeButton == None:
            self.list_buttons[nodeName].config(relief='sunken')
            self.activeButton=nodeName
            #print(self.activeButton)
        else:
            self.list_buttons[self.activeButton].config(relief="raised")
            self.list_buttons[nodeName].config(relief="sunken")
            self.activeButton=nodeName
            #print(self.activeButton)

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

    def make_draggable_host(self,widget):
         widget.bind("<Button-1>", self.click)
         widget.bind("<B1-Motion>", self.drag)
         widget.bind("<Button-3>",self.popup_host)
         widget.bind("<ButtonRelease-1>",self.release)

    def make_draggable_switch(self,widget):
        widget.bind("<Button-1>", self.click)
        widget.bind("<B1-Motion>", self.drag)
        widget.bind("<Button-3>",self.popup_switch)
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
        # for src in self.source.keys():
        #     if (src == widget):
        #          link=self.source[src]
        #
        #          self.canvas.coords(self.source[src],x,y,,)
        #         print(self.source[u])
        # for b in self.dest.keys():
        #     if(b == widget):
        #         self.canvas.coords(self.source[b],x1,y1,x,y)



    def popup_host(self,event):
        item=event.widget
        popup_menu=Menu(self.canvas,tearoff=0)
        #popup_menu.add_command(label="Delete",command=item.destroy())
        popup_menu.add_command(label="Host Properties",command=self.hostProperties)
        popup_menu.post(event.x_root,event.y_root)

    def popup_switch(self,event):
        item=event.widget
        popup_menu=Menu(self.canvas,tearoff=0)
        popup_menu.add_command(label="Switch Properties",command=self.switchProperties)
        popup_menu.post(event.x_root,event.y_root)

    def hostProperties(self):
        fen = Tk()
        fen.geometry('500x500')
        nb = ttk.Notebook(fen)
        frame1=ttk.Frame(nb)
        frame2=ttk.Frame(nb)
        nb.add(frame1,text="Properties")
        nb.add(frame2,text="VLAN Interfaces")
        nb.pack(fill="both",expand="yes")

        label_1=Label(frame1,text="Hostname :",width=20,font=("bold",10))
        label_1.place(x=1,y=20)
        entry_1=Entry(frame1)
        entry_1.place(x=150,y=20)

        label_2=Label(frame1,text="IP Address :",width=20,font=("bold",10))
        label_2.place(x=1,y=50)
        entry_2=Entry(frame1)
        entry_2.place(x=150,y=50)

        label_3=Label(frame1,text="Default Route :",width=20,font=("bold",10))
        label_3.place(x=1,y=80)
        entry_3=Entry(frame1)
        entry_3.place(x=150,y=80)

        label_4=Label(frame1,text="Amount CPU :",width=20,font=("bold",10))
        label_4.place(x=1,y=110)
        entry_4=Entry(frame1)
        entry_4.place(x=150,y=110)
        mb=Menubutton(frame1,text="host",bg="blue",width=8)
        mb.menu=Menu(mb)
        mb["menu"]=mb.menu
        mb.menu.add_command(label="host")
        mb.menu.add_command(label="cfs")
        mb.menu.add_command(label="rt")
        mb.place(x=350,y=110)

        label_5=Label(frame1,text="Cores :",width=20,font=("bold",10))
        label_5.place(x=1,y=140)
        entry_5=Entry(frame1)
        entry_5.place(x=150,y=140)

        label_6=Label(frame1,text="Start Command :",width=20,font=("bold",10))
        label_6.place(x=1,y=170)
        entry_6=Entry(frame1)
        entry_6.place(x=150,y=170)

        label_7=Label(frame1,text="Stop Command :",width=20,font=("bold",10))
        label_7.place(x=1,y=200)
        entry_7=Entry(frame1)
        entry_7.place(x=150,y=200)

        bouton1=Button(frame1,text="OK",width=8,height=2)
        bouton1.place(x=1,y=400)

        bouton2=Button(frame1,text="Cancel",width=8,height=2)
        bouton2.place(x=100,y=400)
        fen.mainloop()

    def switchProperties(self):
        fen = Tk()
        fen.geometry('500x500')

        label_1=Label(fen,text="Hostname :",width=20,font=("bold",10))
        label_1.place(x=0,y=10)
        entry_1=Entry(fen)
        entry_1.place(x=130,y=10)

        label_9=Label(fen,text="External Interface :",width=20,font=("bold",10))
        label_9.place(x=290,y=10)
        bouton5=Button(fen,text="Add")
        bouton5.place(x=440,y=8)

        inter=VerticalScrolledTable(self.interfaceFrame, rows=0, columns=1, title='External Interfaces')

        label_2=Label(fen,text="DPID :",width=20,font=("bold",10))
        label_2.place(x=0,y=40)
        entry_2=Entry(fen)
        entry_2.place(x=110,y=40)

        label_2=Label(fen,text="Enable NetFlow :",width=20,font=("bold",10))
        label_2.place(x=0,y=70)
        bouton2=Checkbutton(fen)
        bouton2.place(x=130,y=70)

        label_3=Label(fen,text="Enable sFlow :",width=20,font=("bold",10))
        label_3.place(x=0,y=100)
        bouton3=Checkbutton(fen)
        bouton3.place(x=130,y=100)

        label_4=Label(fen,text="Switch Type",width=20,font=("bold",10))
        label_4.place(x=0,y=130)
        mb=Menubutton(fen,text="Default",bg="blue",width=8)
        mb.menu=Menu(mb)
        mb["menu"]=mb.menu
        mb.menu.add_command(label="Default")
        mb.menu.add_command(label="Open VSwitch Kernel Mode")
        mb.menu.add_command(label="Indigo Virtual Switch")
        mb.menu.add_command(label="Underspace Switch")
        mb.menu.add_command(label="Underspace Switch in Namespace")
        mb.place(x=130,y=130)

        label_5=Label(fen,text="IP Address :",width=20,font=("bold",10))
        label_5.place(x=0,y=160)
        entry_3=Entry(fen)
        entry_3.place(x=130,y=160)

        label_6=Label(fen,text="DPCTL port :",width=20,font=("bold",10))
        label_6.place(x=0,y=190)
        entry_4=Entry(fen)
        entry_4.place(x=130,y=190)

        label_7=Label(fen,text="Start Command :",width=20,font=("bold",10))
        label_7.place(x=0,y=430)
        entry_5=Entry(fen)
        entry_5.place(x=140,y=430,width=350)

        label_8=Label(fen,text="Stop Command :",width=20,font=("bold",10))
        label_8.place(x=0,y=460)
        entry_6=Entry(fen)
        entry_6.place(x=140,y=460,width=350)

        fen.mainloop()



    #Placer un bouton sur le canevas
    def canvasHandle(self,event):
        x1=event.x
        y1=event.y
        if (self.activeButton == 'Switch'):
            bouton1=Button(self.canvas,image=self.images['Switch'])
            id1=self.canvas.create_window((x1,y1),anchor='center',window=bouton1)
            self.widgetToItem[bouton1]=id1
            self.itemToWidget[id1]=bouton1
            self.buttons_canevas[self.activeButton]=bouton1
            self.make_draggable_switch(self.buttons_canevas[self.activeButton])
            self.nb_widget_canevas+=1
            self.list_buttons['Switch'].config(relief="raised")
            self.activeButton=None
        elif(self.activeButton == 'Host'):
            bouton2=Button(self.canvas,image=self.images['Host'])
            id2=self.canvas.create_window((x1,y1),anchor='center',window=bouton2)
            self.widgetToItem[bouton2]=id2
            self.itemToWidget[id2]=bouton2
            self.buttons_canevas[self.activeButton]=bouton2
            self.make_draggable_host(self.buttons_canevas[self.activeButton])
            self.nb_widget_canevas+=1
            self.list_buttons['Host'].config(relief="raised")
            self.activeButton=None
        elif(self.activeButton == 'Link'):
            for valeur in self.buttons_canevas.values():
                self.make_draggable(self.buttons_canevas[self.activeButton])

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
        #print(item)
        x, y = self.canvas.coords(item)
        self.coordonnees["i0"]=x
        self.coordonnees["j0"]=y
        self.link = self.canvas.create_line(x,y,x,y,width=4,fill='blue',tag='link')
        self.linkWidget=w
        self.source[w]=self.link
        #print(self.source)

    # def createLink(self,event):
    #     w = event.widget
    #     item = self.widgetToItem[w]
    #     #print(item)
    #     x, y = self.canevas.coords(item)
    #     self.coordonnees["i"]=x
    #     self.coordonnees["j"]=y
    #     self.link = self.canevas.create_line(x,y,x,y,width=4,fill='blue',tag='link')
    #     self.linkWidget=w
    #     self.source[w]=self.link
    #     #print(self.source)

    def dragLink(self,event):
        b = self.canvasx( event.x_root ) # coordonnées d'arrivée
        n = self.canvasy( event.y_root ) # coordonnées d'arrivée
        self.canvas.coords(self.link,self.coordonnees["i0"],self.coordonnees["j0"],b,n)

    def finishLink(self,event):
        #we drag from the widget , we use root coordonnees
        src = self.linkWidget
        x = self.canvasx(event.x_root) # coordonnées d'arrivée du lien
        y= self.canvasy(event.y_root) # coordonnées d'arrivée du lien
        target = self.findObject(x,y) # item du widget d'arrivée
        dest1=self.itemToWidget.get(target,None) #widget correspondant à l'item se trouvant à l'arrivée
        if (dest1 != None):
            self.dest[dest1]=self.link
            self.link=None
            self.linkWidget=None
            print(self.dest)
            print(self.source)
        elif(dest1 == None):
            self.canvas.delete( self.link )
            del self.source[src]
            #print(self.source)
            self.link=None
            self.linkWidget=None
        elif (dest1 == src or dest1 in self.source.values()):
            self.canvas.delete( self.link )
            del self.source[src]
            del self.dest[dest1]
            self.link=None
            self.linkWidget=None

    def netImages(self):
        img1=PhotoImage(file="/home/user/Desktop/graph/switch.gif")
        img2=PhotoImage(file="/home/user/Desktop/graph/cursor.png")
        img3=PhotoImage(file="/home/user/Desktop/graph/host.png")
        img4=PhotoImage(file="/home/user/Desktop/graph/line.png")
        img1_mini=img1.subsample(7,8)
        img2_mini=img2.subsample(3,4)
        img3_mini=img3.subsample(4,4)
        img4_mini=img4.subsample(4,4)
        dict_images={'Switch': img1_mini,'Cursor':img2_mini,'Host':img3_mini,'Link':img4_mini}
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
