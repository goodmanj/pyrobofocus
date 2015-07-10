""" Python RoboFocus

Controls RoboFocus focusers.

This Python script relies on Tkinter to provide a GUI.  If it's not installed on
your system, you're in trouble.
"""

import pyrobofocusui
import rfserial
from tkinter import Tk


gui = pyrobofocusui.PyRoboFocusUI(master=Tk())
gui.master.title("PyRoboFocus")
gui.mainloop()
