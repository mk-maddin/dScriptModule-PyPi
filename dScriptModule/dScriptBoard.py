#!/usr/bin/python
# version: 2019.08.09
# author: Martin Kraemer, mk.maddin@gmail.com
# description: 
#   object capturing all incoming command triggers (protocol independend) and trowing events

from .dScriptObject import *
from .dScriptEvent import *
import struct
import socket

class dScriptBoard(object):

    _HostName='Unknown'
    
    _ModuleID='Unknown'
    _SystemFirmwareMajor=0
    _SystemFirmwareMinor=0
    _ApplicationFirmwareMajor=0
    _ApplicationFirmwareMinor=0
    _Volts=0
    _Temperature=0

    _TCPPort=0              #nice to have value
    _TCPProtocol='Unknown'  #nice to have value
    _PhysicalRelays=0
    _ConnectedLights=0
    _ConnectedShutters=0
    _ConnectedSockets=0

    _evt_LightChanged = Event(identifier,state)
    _evt_ShutterChanged = Event(identifier,state)
    _evt_SocketChanged = Event(identifier,state)
    _evt_StatusChanged = Event()

    '''Initialize the dScriptBoard element with at least its IP and port to be able to connect later'''
    def __init__(self, TCP_IP, TCP_PORT=17123):
        logging.debug("dScriptBoard: __init__")
        self.IP = TCP_IP
        self.Port = TCP_PORT
        self.GetHostName()

    '''Send command protocol independend'''
    def __SendProtocol(self,command,arguments):
        logging.debug("dScriptBoard: __SendProtocol: %s | %s",command, arguments)
        if self._Protocol == self._Protocols[4]:    #BinaryAES
            msg=self._GetKeyByValue(command,self._BinaryCommands)
            for a in arguments:
                msg = msg + struct.pack("B",a)
            msg=self._AESEncrypt(msg)
            buf=16  #BinaryAES commands are always 16 bytes
        elif self._Protocol == self._Protocols[4]:    #BinaryAES
            msg=self._GetKeyByValue(command,self._BinaryCommands)
            for a in arguments:
                msg = msg + struct.pack("B",a)
            buf=self._BinaryReturnByteCounts[command]
        else
            raise Exception("Protocol not implemented yet: %s", self._Protocol)
            return False
        return self.__Send(msg,buff)

    '''Send a message to the board''' 
    def __Send(self,msg,buff):
        logging.debug("dScriptBoard: __Send: %s | %s",msg,buff)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.IP, self.Port))
        try:
            s.send(msg)
            data = s.recv(buff)
        except Exception as ex:
            self.__socket.close()
            raise Exception(ex)
            return False
        s.close()
        return data

    '''Check if identifier parameter is valid'''
    def __CheckIdentifier(self,identifier,idtype):
        logging.debug("dScriptBoard: __CheckIdentifier")
        if idtype == 'light':
            identifier2=self._ConnectedLights
        elif idtype =='shutter':
            identifier2=self._ConnectedShutters
        elif idtype =='socket':
            identifier2=self._ConnectedSockets
        elif idtype =='relay':
            identifier2=self._PhysicalRelays
        else:
            identifier2=0
        if identifier <= 0 or identifier  > self._ConnectedLights:
            raise Exception("Maximum connected %s is: %s",idtype, identifier2))
            return False
        return True

    '''Check if we could execute SetXxxx correctly'''
    def __CheckSet(self,returnbyte):
        logging.debug("dScriptBoard: __CheckIdentifier")
        if not returnbyte == '0':
            raise Exception("Could not set value - return %s", returnbyte)
            return False
        return True

    '''Find the hostname of this device - using dns resolution - and write it as an attribute'''
    def GetHostName(self):
        logging.debug("dScriptBoard: GetHostName")
        self._HostName = socket.gethostbyaddr(self.IP)[0]
        if not self._HostName:
            self._HostName = self.IP

    '''Execute the GS, GetStatus command on the board and write its results as attributes'''
    def GetStatus(self):
        logging.debug("dScriptBoard: GetStatus")
        data=self.__SendProtocol('GetStatus',[])
        databytes=self.__ToDataBytes(data)
        databits=self.__ToDataBits(data)

        logging.info("dScriptBoard: %s: Update board status information", self._HostName)
        self._ModuleID=self.__ModuleIDs[databytes[0]]
        self._SystemFirmwareMajor=databytes[1]
        self._SystemFirmwareMinor=databytes[2]
        self._ApplicationFirmwareMajor=databytes[3]
        self._ApplicationFirmwareMinor=databytes[4]
        self._Volts=float(databytes[5])/10.00
        self._Temperature=int(databits[(6*8):(8*8)],2)
        #self._evt_StatusChanged()

    '''Execute the GC, GetConfig command on the board and write its results as attributes'''
    def GetConfig(self):
        logging.debug("dScriptBoard: GetConfig")
        data=self.__SendProtocol('GetConfig',[])
        databytes=self.__ToDataBytes(data)
        databits=self.__ToDataBits(data)

        logging.info("dScriptBoard: %s: Update board config information", self._HostName)
        self._ModuleID=self.__ModuleIDs[databytes[0]]
        self._TCPPort=int(databits[(1*8):(8*8)],2)          # written as "nice to have"
        self._TCPProtocol=self.__Protocols[databytes[3]]    # written as "nice to have"
        self._PhysicalRelays=databytes[4]
        self._ConnectedLights=databytes[5]
        self._ConnectedShutters=databytes[6]
        self._ConnectedSockets=databytes[7]
        #self._evt_StatusChanged()

    '''Execute the GL, GetLight command and print the result into log'''
    def GetLight(self,identifier):
        logging.debug("dScriptBoard: GetLight: %s",identifier)
        if not self.__CheckIdentifier(identifier,'light'):
            return False
        data=self.__SendProtocol('GetLight',[identifier])
        databytes=self.__ToDataBytes(data)
        logging.info("dScriptBoard: %s: Light %s is %s", self._HostName, identifier, self._OnOffState[databytes[0]])
        self._evt_LightChanged(identifier,self._OnOffState[databytes[0]])

    '''Execute the GH, GetShutter command and print the result into log'''
    def GetShutter(self,identifier):
        logging.debug("dScriptBoard: GetShutter: %s",[identifier])
        if not self.__CheckIdentifier(identifier,'shutter'):
            return False
        data=self.__SendProtocol('GetShutter',[identifier])
        databytes=self.__ToDataBytes(data)
        logging.info("dScriptBoard: %s: Shutter %s is %s at level %s%%", self._HostName, identifier, self._ShutterStates[databytes[1]], databytes[0])
        self._evt_ShutterChanged(identifier,self._OnOffState[databytes[0]])

    '''Execute the GC, GetSocket command and print the result into log'''
    def GetSocket(self,identifier):
        logging.debug("dScriptBoard: GetSocket: %s",[identifier])
        if not self.__CheckIdentifier(identifier,'socket'):
            return False
        data=self.__SendProtocol('GetLight',identifier)
        databytes=self.__ToDataBytes(data)
        logging.info("dScriptBoard: %s: Socket %s is %s", self._HostName, identifier, self._OnOffState[databytes[0]])
        self._evt_SocketChanged(identifier,self._OnOffState[databytes[0]])

    '''Execute the SL, SetLight command to define a light status'''
    def SetLight(self,identifier,state):
        logging.debug("dScriptBoard: SetLight: %s | %s",identifier,state)
        if not self.__CheckIdentifier(identifier,'light'):
            return False
        data=self.__SendProtocol('SetLight',[identifier,self._GetKeyByValue(state.lower())])
        databytes=self.__ToDataBytes(data)
        return self.__CheckSet(self.__ToDataBytes(data)[0])

    '''Execute the SH, SetShutter command to define a shutter status'''
    def SetShutter(self,identifier,state):
        logging.debug("dScriptBoard: SetShutter: %s | %s",identifier,state)
        if not self.__CheckIdentifier(identifier,'shutter'):
            return False
        if state == 'open':
            state = 100
        elif state == 'closed':
            state = 0
        elif state > 100: #state can be max 100 = Fully Open
            state = 100
        elif state < 0: #state can be min 0 = Fully Closed
            state = 0
        data=self.__SendProtocol('SetShutter',[identifier,state])
        databytes=self.__ToDataBytes(data)
        return self.__CheckSet(self.__ToDataBytes(data)[0])

    '''Execute the SC, SetSocket command to define a socket status'''
    def SetSocket(self,identifier,state):
        logging.debug("dScriptBoard: SetSocket: %s | %s",identifier,state)
        if not self.__CheckIdentifier(identifier,'socket'):
            return False
        data=self.__SendProtocol('SetSocket',[identifier,self._GetKeyByValue(state.lower())])
        databytes=self.__ToDataBytes(data)
        return self.__CheckSet(self.__ToDataBytes(data)[0])
