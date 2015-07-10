""" DomeControlUI

Tkinter user interface for Astrohaven dome control.

"""
import time
import rfserial
import serialist

from tkinter import *

class Log(Text):
    """A text widget that can't be edited by the user."""
    def __init__(self,master=None):
        Text.__init__(self,master)
        self.config(state=DISABLED,wrap=WORD)
    def insert(self, index, chars, *args):
        """Add text to the widget without letting the user type in it."""
        self.config(state=NORMAL)
        Text.insert(self,index, chars, args)
        self.config(state=DISABLED)        
    def delete(self, index1, index2=None):
        """Delete text from the widget without letting the user type in it."""
        self.config(state=NORMAL)
        Text.delete(self, index1, index2)
        self.config(state=DISABLED)
    def log(self, chars):
        """Add text to the end of the widget and make sure it's visible."""
        self.insert(END, chars+'\n')
        self.see(END)
        self.update()

class PyRoboFocusUI(Frame):
    def __init__(self, master=None):
        Frame.__init__(self,master)
        self.rf = None
        self.grid()
        self.createWidgets()
        
    def createWidgets(self):
        self.quitbutton = Button (self, text='Quit', command = self.quit)
        self.quitbutton.grid(row=0,column=0)

        self.portcontainer = Frame(self)
        self.portcontainer.grid(column=1,row=0,columnspan=2)
        self.portLabel = Label(self, text='Serial Port:',justify=RIGHT)
        self.portLabel.pack(in_=self.portcontainer,side='left')

        self.stepsLabel = Label(self, text='Step:')
        self.stepsLabel.grid(row=1, column=1)
        self.steps = StringVar()
        self.steps.set('50')
        self.oldsteps = self.steps.get()        
        self.numstepsEntry = Entry(self,textvariable=self.steps)
        self.numstepsEntry.grid(row=2,column=1)

        self.moveinButton = Button (self, text='In', command = self.movein)
        self.moveinButton.grid(row=2,column=0)

        self.moveoutButton = Button (self, text='Out', command = self.moveout)
        self.moveoutButton.grid(row=2,column=2)

        self.positiontext = StringVar()
        self.positiontext.set('Not Connected')
        self.postext = Label(self, text='Position:')
        self.postext.grid(column=0,row=3)
        self.positionlabel = Label (self, textvariable=self.positiontext,height=2,width=15)
        self.positionlabel.grid(column=1,row=3)

        self.powcontainer = Frame(self)
        self.powcontainer.grid(column=0,row=4,columnspan=3)

        self.powtext = Label(self, text='Remote Power:')
        self.powtext.pack(in_=self.powcontainer,side="left")

        self.pow = [IntVar(),IntVar(),IntVar(),IntVar()]
        self.powCheck1 = Checkbutton (self, text='1', variable = self.pow[0], command = lambda: self.togglepow(1))
        self.powCheck1.pack(in_=self.powcontainer,side="left")

        self.powCheck2 = Checkbutton (self, text='2', variable = self.pow[1], command = lambda: self.togglepow(2))   
        self.powCheck2.pack(in_=self.powcontainer,side="left")

        self.powCheck3 = Checkbutton (self, text='3', variable = self.pow[2], command = lambda: self.togglepow(3))
        self.powCheck3.pack(in_=self.powcontainer,side="left")

        self.powCheck4 = Checkbutton (self, text='4', variable = self.pow[3], command = lambda: self.togglepow(4))
        self.powCheck4.pack(in_=self.powcontainer,side="left")

        self.messages = Log(self)
        self.messages.config(width=30,height=4)
        self.messages.grid(row=5,column=0,columnspan=3)



        """serialist.Serialist() returns a list of active serial ports on this machine.
        This list is not updated while PyRoboFocus is running."""
        self.port = StringVar()
        portList = serialist.Serialist()
        focuserPorts = [];
        self.messages.log('Please wait...')
        for port in portList:
            self.update()
            self.messages.log('Scanning '+port+' for focusers.')
            rf = rfserial.RFSerial(port)
            if rf.ready:
                focuserPorts.append(port)
                rf.closeconn()
        if not focuserPorts:
            self.messages.log('No focusers found.  Connect a focuser and restart.\n')
            self.rf = None
            focuserPorts = ['NONE FOUND']
            self.port.set(focuserPorts[0])
        else:
            self.port.set(focuserPorts[0])
            self.updateport()
        self.portmenu = OptionMenu (self, self.port, *focuserPorts, command=self.updateport)
        self.portmenu.pack(in_=self.portcontainer,side='left')

    def quit(self):
        Frame.quit(self)
        
    def updateport(self,event=None):
        """Handle a change in the active serial port.  Close the current port
        if it's open and attempt to open the new one."""
        self.messages.log('Looking for focuser on '+str(self.port.get())+'...')
        if self.rf is not None and self.rf.ready:
            self.rf.closeconn()
        self.rf = rfserial.RFSerial(str(self.port.get()))
        if self.rf is not None and self.rf.ready:
            self.messages.log('Connected to focuser on '+str(self.port.get()))
            self.positiontext.set(str(self.rf.querypos()))
            pow = self.rf.queryrempow()
            self.pow[0].set(int(pow[0]))
            self.pow[1].set(int(pow[1]))
            self.pow[2].set(int(pow[2]))
            self.pow[3].set(int(pow[3]))
        else:
            self.messages.log("Can't connect to focuser on "+str(self.port.get()))
            self.positiontext.set('Not Connected')

    def updatepos(self,event=None):
        self.positiontext.set(str(self.rf.querypos()))
        
    def movein(self,event=None):
        steps = self.validatesteps()
        if self.rf is not None and self.rf.ready:
            self.messages.log('Moving in %d steps'%steps)
            self.positiontext.set('Moving')
            self.update()
            newpos = self.rf.stepin(int(steps))
            self.positiontext.set(str(newpos))

    def moveout(self,event=None):
        steps = self.validatesteps()
        if self.rf is not None and self.rf.ready:
            self.messages.log('Moving out %d steps'%steps)
            self.positiontext.set('Moving')
            self.update()
            newpos = self.rf.stepout(steps)
            self.positiontext.set(str(newpos))

    def validatesteps(self):
        try:
            s = int(self.steps.get())
        except:
            s = 0
        if (s > 0) & (s < 2000):
            self.oldsteps = s
        else:
            s = self.oldsteps
            self.steps.set(str(s))
            self.update()
        return int(s)

    def togglepow(self,channel):
        """Handle a change in the state of the "Remote Power" checkboxes."""
        if self.rf is not None:
            newstatus = bool(self.pow[channel-1].get())
            finalstatus = self.rf.setrempow(channel-1,newstatus)
            self.messages.log('Remote power channel %d set to '%(channel)+str(finalstatus))
        else:
            self.messages.log('Not connected to a focuser.')
            