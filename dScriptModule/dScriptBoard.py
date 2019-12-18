#!/usr/bin/python
# version: 2019.12.13
# author: Martin Kraemer, mk.maddin@gmail.com
# description: 
#   object capturing all incoming command triggers (protocol independend) and trowing events

from .dScriptObject import *
import struct
import socket

class dScriptBoard(dScriptObject):

    _HostName=None
    ConnectionTimeout = 10

    _ModuleID='Unknown'
    _SystemFirmwareMajor=0
    _SystemFirmwareMinor=0
    _ApplicationFirmwareMajor=0
    _ApplicationFirmwareMinor=0
    _Volts=0
    _Temperature=0

    _CustomFirmeware=False
    _PhysicalRelays=0
    _ConnectedLights=0
    _ConnectedShutters=0
    _ConnectedSockets=0
    _MACAddress='00:00:00:00:00:00'
    _VirtualRelays=32 #this is always 32

    _EventHandlers = { 'status':[], 'config':[], 'light':[], 'shutter':[], 'socket':[] }

    '''Initialize the dScriptBoard element with at least its IP and port to be able to connect later'''
    def __init__(self, TCP_IP, TCP_PORT=17123, PROTOCOL='binary'):
        #logging.debug("dScriptBoard: __init__")
        self.IP = TCP_IP
        self.Port = TCP_PORT
        self.SetProtocol(PROTOCOL)
        self.GetHostName()

    '''Send command protocol independend'''
    def __SendProtocol(self,command,arguments):
        logging.debug("dScriptBoard: __SendProtocol: %s | %s",command, arguments)
        if self._Protocol == self._Protocols[4]:    #BinaryAES
            msg=struct.pack("B",self._GetKeyByValue(command,self._DecimalCommands))
            for a in arguments:
                msg = msg + struct.pack("B",a)
            msg=self._AESEncrypt(msg)
            buff=16  #BinaryAES commands are always 16 bytes
        elif self._Protocol == self._Protocols[3]:    #Binary
            msg=struct.pack("B",self._GetKeyByValue(command,self._DecimalCommands))
            for a in arguments:
                msg = msg + struct.pack("B",a)
            buff=self._BinaryReturnByteCounts[command]
        else:
            raise Exception("Protocol not implemented yet: %s", self._Protocol)
            return False
        return self.__Send(msg,buff)

    '''Send a message to the board''' 
    def __Send(self,msg,buff):
        logging.debug("dScriptBoard: __Send: %s | %s",msg,buff)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.ConnectionTimeout)
        s.connect((self.IP, self.Port))
        try:
            s.send(msg)
            data = s.recv(buff)
        except Exception as ex:
            s.close()
            raise Exception(ex)
            return False
        s.close()
        return data

    '''Check if identifier parameter is valid'''
    def __CheckIdentifier(self,identifier,idtype):
        #logging.debug("dScriptBoard: __CheckIdentifier")
        if idtype == 'light':
            identifier2=self._ConnectedLights
        elif idtype =='shutter':
            identifier2=self._ConnectedShutters
        elif idtype =='socket':
            identifier2=self._ConnectedSockets
        elif idtype =='relay':
            if self._CustomFirmeware:
                identifier2=self._PhysicalRelays
            else:
                identifier2=self._VirtualRelays
        else:
            identifier2=0
        if identifier <= 0 or identifier  > self._ConnectedLights:
            raise Exception("Maximum connected %s is: %s",idtype, identifier2)
            return False
        return True

    '''Check if we could execute SetXxxx correctly'''
    def __CheckSet(self,returnbyte):
        #logging.debug("dScriptBoard: __CheckIdentifier")
        if not returnbyte == 0:
            raise Exception("Could not set value - return %s", returnbyte)
            return False
        return True

    '''Find the hostname of this device - using dns resolution - and write it as an attribute'''
    def GetHostName(self):
        #logging.debug("dScriptBoard: GetHostName")
        name = socket.gethostbyaddr(self.IP)[0]
        if name:
            self._HostName = name.split('.')[0]
        elif not self._HostName:
            self._HostName = self.IP

    '''Initialize the board and write its results as attributes'''
    def InitBoard(self):
        self.GetHostName()
        self.GetStatus()
        self.GetConfig()

    '''Execute the GS, GetStatus command on the board and write its results as attributes'''
    def GetStatus(self):
        #logging.debug("dScriptBoard: GetStatus")
        data=self.__SendProtocol('GetStatus',[])
        databytes=self._ToDataBytes(data)
        databits=self._ToDataBits(data)

        logging.info("dScriptBoard: %s: Update board status information", self._HostName)
        self._ModuleID=self._Modules[databytes[0]]
        self._SystemFirmwareMajor=databytes[1]
        self._SystemFirmwareMinor=databytes[2]
        self._ApplicationFirmwareMajor=databytes[3]
        self._ApplicationFirmwareMinor=databytes[4]
        self._Volts=float(databytes[5])/10.00
        self._Temperature=float(int(databits[(6*8):(8*8)],2)/10.00)
        self._throwEvent(self._HostName, 'status')

    '''Execute the GC, GetConfig command on the board and write its results as attributes'''
    def GetConfig(self):
        #logging.debug("dScriptBoard: GetConfig")
        try:
            data=self.__SendProtocol('GetConfig',[])
        except:
            logging.info("dScriptBoard: %s: Contains default firmware", self._HostName)
            self._CustomFirmeware=False
            return False
        self._CustomFirmeware=True
        databytes=self._ToDataBytes(data)
        databits=self._ToDataBits(data)

        logging.info("dScriptBoard: %s: Update board config information", self._HostName)
        self._PhysicalRelays=databytes[0]
        self._ConnectedLights=databytes[1]
        self._ConnectedShutters=databytes[2]
        self._ConnectedSockets=databytes[3]
        databytes[4]=str(hex(databytes[4]).split('x')[-1])
        databytes[5]=str(hex(databytes[5]).split('x')[-1])
        databytes[6]=str(hex(databytes[6]).split('x')[-1])
        databytes[7]=str(hex(databytes[7]).split('x')[-1])
        databytes[8]=str(hex(databytes[8]).split('x')[-1])
        databytes[9]=str(hex(databytes[9]).split('x')[-1])
        self._MACAddress=databytes[4]+':'+databytes[5]+':'+databytes[6]+':'+databytes[7]+':'+databytes[8]+':'+databytes[9]
        self._throwEvent(self._HostName, 'config')

    #'''Execute the GR, GetRelay command and print the result into log'''
    #def GetRelay(self,identifier):
    #    #logging.debug("dScriptBoard: GetLight: %s",identifier)
    #    if not self._CustomFirmeware:
    #        return False
    #    if not self.__CheckIdentifier(identifier,'light'):
    #        return False
    #    data=self.__SendProtocol('GetLight',[identifier])
    #    databytes=self._ToDataBytes(data)
    #    logging.info("dScriptBoard: %s: Light %s is %s", self._HostName, identifier, self._OnOffStates[databytes[0]])
    #    self._throwEvent(self._HostName, 'light', identifier, self._OnOffStates[databytes[0]])

    '''Execute the GL, GetLight command and print the result into log'''
    def GetLight(self,identifier):
        #logging.debug("dScriptBoard: GetLight: %s",identifier)
        if not self._CustomFirmeware:
            return False
        if not self.__CheckIdentifier(identifier,'light'):
            return False
        data=self.__SendProtocol('GetLight',[identifier])
        databytes=self._ToDataBytes(data)
        logging.info("dScriptBoard: %s: Light %s is %s", self._HostName, identifier, self._OnOffStates[databytes[0]])
        self._throwEvent(self._HostName, 'light', identifier, self._OnOffStates[databytes[0]])
        return self._OnOffStates[databytes[0]]

    '''Execute the GH, GetShutter command and print the result into log'''
    def GetShutter(self,identifier):
        #logging.debug("dScriptBoard: GetShutter: %s",[identifier])
        if not self._CustomFirmeware:
            return False
        if not self.__CheckIdentifier(identifier,'shutter'):
            return False
        data=self.__SendProtocol('GetShutter',[identifier])
        databytes=self._ToDataBytes(data)
        logging.info("dScriptBoard: %s: Shutter %s is %s at level %s%%", self._HostName, identifier, self._ShutterStates[databytes[1]], databytes[0])
        self._throwEvent(self._HostName, 'shutter', identifier, databytes[0])
        return [databytes[0],self._ShutterStates[databytes[1]]]

    '''Execute the GC, GetSocket command and print the result into log'''
    def GetSocket(self,identifier):
        #logging.debug("dScriptBoard: GetSocket: %s",[identifier])
        if not self._CustomFirmeware:
            return False
        if not self.__CheckIdentifier(identifier,'socket'):
            return False
        data=self.__SendProtocol('GetSocket',[identifier])
        databytes=self._ToDataBytes(data)
        logging.info("dScriptBoard: %s: Socket %s is %s", self._HostName, identifier, self._OnOffStates[databytes[0]])
        self._throwEvent(self._HostName, 'socket', identifier, self._OnOffStates[databytes[0]])
        return self._OnOffStates[databytes[0]]

    '''Execute the SR, SetRelay command to define a relay status'''
    def SetRelay(self,identifier,state):
        #logging.debug("dScriptBoard: SetRelay: %s | %s",identifier,state)
        if not self.__CheckIdentifier(identifier,'relay'):
            return False
        data=self.__SendProtocol('SetRelay',[identifier,self._GetKeyByValue(state.lower(),self._OnOffStates)])
        databytes=self._ToDataBytes(data)
        return self.__CheckSet(self._ToDataBytes(data)[0])

    '''Execute the SL, SetLight command to define a light status'''
    def SetLight(self,identifier,state):
        #logging.debug("dScriptBoard: SetLight: %s | %s",identifier,state)
        if not self._CustomFirmeware: # fallback to legacy relay action
            return self.SetRelay(identifier,state)
        if not self.__CheckIdentifier(identifier,'light'):
            return False
        data=self.__SendProtocol('SetLight',[identifier,self._GetKeyByValue(state.lower(),self._OnOffStates)])
        databytes=self._ToDataBytes(data)
        return self.__CheckSet(self._ToDataBytes(data)[0])

    '''Execute the SH, SetShutter command to define a shutter status'''
    def SetShutter(self,identifier,state):
        #logging.debug("dScriptBoard: SetShutter: %s | %s",identifier,state)
        if not self._CustomFirmeware: # fallback to legacy relay action
            return self.SetRelay(identifier,state)
        if not self.__CheckIdentifier(identifier,'shutter'):
            return False
        if state == 'open':
            state = 100
        elif state == 'close':
            state = 0
        elif state == 'stop' or state == 255: # stop the shutter at current state
            state = 255
        elif state > 100: #state can be max 100 = Fully Open
            state = 100
        elif state < 0: #state can be min 0 = Fully Closed
            state = 0
        data=self.__SendProtocol('SetShutter',[identifier,state])
        databytes=self._ToDataBytes(data)
        return self.__CheckSet(self._ToDataBytes(data)[0])

    '''Execute the SC, SetSocket command to define a socket status'''
    def SetSocket(self,identifier,state):
        #logging.debug("dScriptBoard: SetSocket: %s | %s",identifier,state)
        if not self._CustomFirmeware: # fallback to legacy relay action
            return self.SetRelay(identifier,state)
        if not self.__CheckIdentifier(identifier,'socket'):
            return False
        data=self.__SendProtocol('SetSocket',[identifier,self._GetKeyByValue(state.lower(),self._OnOffStates)])
        databytes=self._ToDataBytes(data)
        return self.__CheckSet(self._ToDataBytes(data)[0])
