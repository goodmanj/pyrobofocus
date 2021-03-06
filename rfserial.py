"""Communicates with an Robofocus telescope focuser through a serial port.
Serial port must be passed in at instance creation."""

import serial
import time

class RFSerial:

    listen_timeout = 2   # Max number of seconds to wait for a response
    
    def __init__(self,comport=None):
        self.ready = False
        if comport is not None:
            self.openconn(comport)

    def openconn(self,comport):
        """Open a serial connection on port comport.  Asks for version to confirm
           that the device is an active Robofocus."""
        self.ready = False
        try:
            self.ser = serial.Serial(comport,9600,timeout=1)
            self.ready = True
        except:
            print('Failed to open serial port ',comport)     
            self.ready = False
        if self.ready:
            # 
            if self.version() is None:
                print('Focuser is not responding.')
                self.ready = False
            self.ser.flush()

    def sendreceive(self,msg):
        """Send message "msg" to Robofocus, return the response.  Calculates
        checksum automatically."""
        msgwithcheck = msg + bytes([sum(msg)&255])
        self.ser.flushInput()
        self.ser.write(msgwithcheck)
        """If it's a move command, focuser may send some 'I' and 'O' chars before
        the reply code."""
        ch = self.ser.read(1)
        while (ch == b'O') | (ch == b'I'):
            ch = self.ser.read(1)
        reply = ch + self.ser.read(8)
        return reply

    def version(self):
        """Query version of Robofocus control firmware."""
        msg = b'FV000000'
        reply = self.sendreceive(msg)
        if (len(reply) == 9) & (reply[0:2] == b'FV'):
            return reply[2:8]
        else:
            return None

    def querypos(self):
        """Query current position of focuser"""
        msg = b'FG000000'
        reply = self.sendreceive(msg)
        if len(reply) > 0:
            return int(reply[2:8])
        else:
            return None
    
    def gotopos(self,pos):
        """Goto position "pos".  Returns final position."""
        reply = b''
        if (pos < 65000) & (pos > 0):
            msg = bytes('FG%06d'%pos,'ascii')
            reply = self.sendreceive(msg)
        if len(reply) > 0:
            ch = self.ser.read(1)
            while (ch == b'O') | (ch == b'I'):
                ch = self.ser.read(1)
            reply = ch + self.ser.read(8)
            if len(reply) > 0:
                return int(reply[2:8])
            else:
                return None
        else:
            return None

    def stepin(self,steps):
        """Step inward "steps" steps.  Returns new position."""
        reply = b''
        if (steps < 65000) & (steps > 0):
            msg = bytes('FI%06d'%steps,'ascii')
            reply = self.sendreceive(msg)
        if len(reply) > 0:
                return int(reply[2:8])
        else:
                return None

    def stepout(self,steps):
        """Step inward "steps" steps.  Returns new position."""
        reply = b''
        if (steps < 65000) & (steps > 0):
            msg = bytes('FO%06d'%steps,'ascii')
            reply = self.sendreceive(msg)
        if len(reply) > 0:
                return int(reply[2:8])
        else:
                return None

    def queryrempow(self):
        """Get remote power status.  Returns a list of booleans."""
        msg = b'FP000000'
        reply = self.sendreceive(msg)[0:8].decode()
        """ 1 = ON, 2=OFF for JCG's remote power box design."""
        return [reply[4]=='1',reply[5]=='1',reply[6]=='1',reply[7]=='1']

    def setrempow(self,channel,onoff):
        """Set remote power status for channel to onoff. channels are numbered
        starting from zero."""
        msg = b'FP000000'
        status = list(self.sendreceive(msg)[4:8].decode())
        """ 1 = ON, 2 = OFF for JCG's remote power box design."""
        if (onoff):
            status[channel] = '1'
        else:
            status[channel] = '2'
        msg = bytes('FP00'+''.join(status),'ascii')
        reply = self.sendreceive(msg)[4:8].decode()
        return reply[channel]=='1'
    
    def closeconn(self):
        self.ser.close()
        self.ready = False
