
from tkinter import *

root = Tk()

opts = ('bacon', 'cereal', 'eggs')

oMenuWidth = len(max(opts, key=len))

v = StringVar(root)
v.set(opts[0])
oMenu = OptionMenu(root, v, *opts)
oMenu.config(width=oMenuWidth)
oMenu.grid()

mainloop()

root.mainloop()
