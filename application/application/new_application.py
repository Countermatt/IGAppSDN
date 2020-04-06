from tkinter import *
from PIL import Image,ImageTk
#from Tkinter import ttk
from tkinter import ttk
from tkinter import filedialog
import logging
import os
import json
from functools import partial
from subprocess import call
from time import sleep

logging.basicConfig(level=logging.INFO)

class Interface():

#Initialisation de l'interface---------------------------------------------------------------------
    def __init__(self,window):
        self.create_menu_bar(window)
        self.create_main_panel(window)
#--------------------------------------------------------------------------------------------------

#Creation de la barre des taches-------------------------------------------------------------------

    def create_menu_bar(self,window):
        mainmenu = Menu(window)

        sousMenuFile=Menu(mainmenu,tearoff=0)
        sousMenuFile.add_command(label="New")
        sousMenuFile.add_command(label="Open")
        sousMenuFile.add_command(label="Save")
        sousMenuFile.add_command(label="Export level 2 script")
        sousMenuFile.add_command(label="Quit")
        mainmenu.add_cascade(label="File",menu=sousMenuFile)

        sousMenuEdit=Menu(mainmenu,tearoff=0)
        sousMenuEdit.add_command(label="Cut")
        sousMenuEdit.add_command(label="Preferences")
        mainmenu.add_cascade(label='Edit',menu=sousMenuEdit)

        sousMenuRun=Menu(mainmenu,tearoff=0)
        sousMenuRun.add_command(label="Run")
        sousMenuRun.add_command(label="Stop")
        sousMenuRun.add_command(label="Show OVS Summary")
        sousMenuRun.add_command(label="Root Terminal")
        mainmenu.add_cascade(label='Run',menu=sousMenuRun)

        sousMenuCommand=Menu(mainmenu,tearoff=0)
        sousMenuCommand.add_command(label="Dump")
        sousMenuCommand.add_command(label="Ifconfig")
        sousMenuCommand.add_command(label="Ping all hosts")
        sousMenuCommand.add_command(label="Ping pair")
        sousMenuCommand.add_command(label="Iperf")
        sousMenuCommand.add_command(label="List of Nodes")
        sousMenuCommand.add_command(label="Nodes and links informations")
        mainmenu.add_cascade(label='Command',menu=sousMenuCommand)

        sousMenuHelp=Menu(mainmenu,tearoff=0)
        sousMenuHelp.add_command(label="About NetView")
        mainmenu.add_cascade(label='Help',menu=sousMenuHelp)

        window.config(menu=mainmenu)
#--------------------------------------------------------------------------------------------------

#Creation des onglets------------------------------------------------------------------------------
    def create_main_notebook(self,window):
        notebook = ttk.Notebook(window)

        notebook.grid(row=1, column=0, columnspan=50, rowspan=49, sticky='NESW')
        page1 = self.create_topo_panel(notebook)
        notebook.add(page1, text= 'Topologie')

        page2 = Canvas(notebook,width='900', height = '800',bg='white')
        notebook.add(page2, text='Performances')

        page3 = Canvas(notebook,width='900', height = '800',bg='white')
        notebook.add(page3, text='Sécurité')

#--------------------------------------------------------------------------------------------------

#creation du menu principal------------------------------------------------------------------------

    def create_main_panel(self,window):

        main_panel = PanedWindow(window, orient = HORIZONTAL)
        main_panel.pack(side = TOP, expand = Y, fill = BOTH, pady = 2, padx = 2)

        menu_main = Canvas(window,width='75', height = '800',bg='light grey')
        main_panel.add(menu_main)
        Button(menu_main, text = 'New', bg='grey',width='7').pack(side = TOP, padx = 5, pady = 5)
        Button(menu_main, text = 'Load', bg='grey',width='7').pack(side = TOP, padx = 5, pady = 5)
        Button(menu_main, text = 'Save', bg='grey',width='7').pack(side = TOP, padx = 5, pady = 5)
        Button(menu_main, text = 'Export', bg='grey',width='7').pack(side = TOP, padx = 5, pady = 5)
        Button(menu_main, text = 'Start', bg='green',width='7').pack(side = TOP, padx = 5, pady = 5)
        Button(menu_main, text = 'Stop', bg='red',width='7').pack(side = TOP, padx = 5, pady = 5)

        main_notebook = ttk.Frame(width='925', height = '800')
        self.create_main_notebook(main_notebook)
        main_panel.add(main_notebook)
        main_panel.pack()
#--------------------------------------------------------------------------------------------------

#Creation du canevas de topologie------------------------------------------------------------------

    def create_topo_panel(self,window):
        canvas_panel = PanedWindow(window, orient = HORIZONTAL)
        canvas_panel.pack(side = TOP, expand = Y, fill = BOTH, pady = 2, padx = 2)

        img_switch = PhotoImage(file = "ressources/switch.gif")
        img_controleur = PhotoImage(file = "ressources/controleur.png")
        img_host = PhotoImage(file = "ressources/host.png")
        img_line = PhotoImage(file = "ressources/line.png")
        img_legacyrouteur = PhotoImage(file = "ressources/legacyRouter.png")
        img_legacyswitch = PhotoImage(file = "ressources/legacyswitch.png")
        img_logo = PhotoImage(file = "netview_logo.png")


        menu_topo = Canvas(canvas_panel,width='75', height = '800',bg='white')
        button_switch = Button(menu_topo,text = "switch",width='4',height='3').pack(side = TOP, padx = 5, pady = 5)
        button_1 = Button(menu_topo,width='75',height='75')
        button_1.config(relief="raised")
        button_1.config(image = img_logo)
        button_1.pack(side = TOP, padx = 5, pady = 5)
        Button(menu_topo,text = "switch",width='4',height='3').pack(side = TOP, padx = 5, pady = 5)
        Button(menu_topo,text = "switch",width='4',height='3').pack(side = TOP, padx = 5, pady = 5)
        Button(menu_topo,text = "switch",width='4',height='3').pack(side = TOP, padx = 5, pady = 5)
        Button(menu_topo,text = "switch",width='4',height='3').pack(side = TOP, padx = 5, pady = 5)
        canvas_panel.add(menu_topo)




        canvas_notebook = Canvas(canvas_panel,width='800', height = '800', bg='white')
        canvas_panel.add(canvas_notebook)

        canvas_panel.pack()

        return canvas_panel

#--------------------------------------------------------------------------------------------------



#lancement de l'application------------------------------------------------------------------------
def main():
    fenetre= Tk()
    fenetre.title('New Miniedit')
    fenetre['bg']="grey"
    fenetre.geometry("1000x800+350+400")

    interface = Interface(fenetre)
    fenetre.mainloop()

if __name__ == '__main__':
    main()
