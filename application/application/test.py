from tkinter import *
from tkinter import ttk

main = Tk()
main.title('Notebook demo')
main.geometry('500x500')


rows = 0
while rows <50:
    main.rowconfigure(rows, weight=1)
    main.columnconfigure(rows, weight=1)
    rows +=1

nb = ttk.Notebook(main)
nb.grid(row=1, column=0, columnspan=50, rowspan=49, sticky='NESW')

page1 = ttk.Frame(nb)
nb.add(page1, text= 'Tab1')

page2 = ttk.Frame(nb)
nb.add(page2, text='Tab2')

main.mainloop()
