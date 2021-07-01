#!/usr/bin/python
# version: 2021.06.30
# author: Martin Kraemer, mk.maddin@gmail.com
# description: 
#   object capturing all incoming command triggers (protocol independend) and trowing events

from .dScriptObject import *
import struct
import socket
from Crypto import Random
from Crypto.Cipher import AES

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
    _ConnectedMotionSensors=0
    _ConnectedButtons=0
    _MACAddress='00:00:00:00:00:00'
    _VirtualRelays=32 #this is always 32

    _EventHandlers = { 'status':[], 'config':[], 'light':[], 'shutter':[], 'socket':[], 'motion':[], 'button':[] }

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
        msg=struct.pack("B",self._GetKeyByValue(command,self._DecimalCommands))
        for a in arguments:
            msg = msg + struct.pack("B",a)
        if self._Protocol == self._Protocols[4] and self._IsInList(msg[0], self._AESNonceCommands):    #BinaryAES and command with NONCE
            msg=self._AESEncrypt(msg)
            data=self.__Send(msg,16) #BinaryAES commands always return 16 bytes
            data=self._AESDecrypt(data,self._GetKeyByValue(command,self._DecimalCommands))
            return data[:self._BinaryReturnByteCounts[command]] # return only the number of bytes usually returend by Binary protocol
        elif self._Protocol == self._Protocols[3] or self._Protocol == self._Protocols[4]:    #Binary or BinaryAES but command without NONCE
            return self.__Send(msg,self._BinaryReturnByteCounts[command])
        else:
            raise Exception("Protocol not implemented yet: %s", self._Protocol)
            return False

    '''Encrypt a message using AES encryption'''
    def _AESEncrypt(self,msg):
        #logging.debug("dScriptBoard: _AESEncrypt: %s", msg)
        #logging.debug("dScriptBoard: extend msg to 12 Bytes: %s", msg)
        while len(msg) < 12:
            msg = msg + struct.pack("B",0)
        #logging.debug("dScriptBoard: msg extended: %s", msg)
        if msg[0] == self._AESNonceInitCMD:
            #logging.debug("dScriptBoard: %s: Initialize Nonce command", self._HostName)
            msg = msg + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) # just add 0 for initalize
            self._Nonce = '' # reset nonce to prevent duplicate usage
        elif self._IsInList(msg[0], self._AESNonceCommands):
            #logging.debug("dScriptBoard: %s: Command requiring Nonce", self._HostName)
            if not self._Nonce:
                logging.info("dScriptBoard: %s: Need to (re)initial Nonce value", self._HostName)
                self.GetStatus()
            if not self._Nonce:
                logging.error("dScriptBoard: %s: Could not receive Nonce", self._HostName)
                return False
            msg = msg + self._Nonce
            self._Nonce = '' # reset nonce to prevent duplicate usage
        else:
            #logging.debug("dScriptBoard: %s: Command not using Nonce", self._HostName)
            msg = msg + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) # just add 0 for unneeded
        #logging.debug("dScriptBoard: msg to encrypt: %s", msg)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self._AESKey, AES.MODE_CBC, iv)
        msg = iv + cipher.encrypt(msg)
        #logging.debug("dScriptBoard: msg encrypted: %s", msg)
        return msg 

    '''Decrypt a message using AES encryption'''
    def _AESDecrypt(self,data,binaryid):
        #logging.debug("dScriptBoard: _AESDecrypt: %s", data)
        cipher = AES.new(self._AESKey, AES.MODE_CBC, data[:AES.block_size])
        data = cipher.decrypt(data[AES.block_size:])
        if self._IsInList(binaryid, self._AESNonceCommands):
            logging.debug("dScriptBoard: %s: Update Nonce value: %s", self._HostName, data[12:])
            self._Nonce = data[12:]
        #logging.debug("dScriptBoard: data decrypted: %s", data)
        return data

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
        elif idtype =='motion':
                identifier2=self._ConnectedMotionSensors
        elif idtype =='button':
                identifier2=self._ConnectedButtons
        else:
            identifier2=0
        if identifier <= 0 or identifier > identifier2:
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
            data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # on BinaryAES all data returned is 0 (so emulate bad return here)
        if data[6] == 0: # data[6] is the number of physical arrays - this should never be 0
            logging.info("dScriptBoard: %s: Contains default firmware", self._HostName)
            self._CustomFirmeware=False
            return False
        self._CustomFirmeware=True
        databytes=self._ToDataBytes(data)
        databits=self._ToDataBits(data)

        logging.info("dScriptBoard: %s: Update board config information", self._HostName)
        databytes[0]=str(hex(databytes[0]).split('x')[-1])
        databytes[1]=str(hex(databytes[1]).split('x')[-1])
        databytes[2]=str(hex(databytes[2]).split('x')[-1])
        databytes[3]=str(hex(databytes[3]).split('x')[-1])
        databytes[4]=str(hex(databytes[4]).split('x')[-1])
        databytes[5]=str(hex(databytes[5]).split('x')[-1])
        self._MACAddress=databytes[0]+':'+databytes[1]+':'+databytes[2]+':'+databytes[3]+':'+databytes[4]+':'+databytes[5]
        self._PhysicalRelays=databytes[6]
        self._ConnectedLights=databytes[7]
        self._ConnectedShutters=databytes[8]
        self._ConnectedSockets=databytes[9]
        self._ConnectedMotionSensors=databytes[10]
        self._ConnectedButtons=databytes[11]
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
    
    '''Execute the GM, GetMotion command and print the result into log'''
    def GetMotion(self,identifier):
        logging.debug("dScriptBoard: GetMotion: %s",[identifier])
        if not self._CustomFirmeware:
            return False
        if not self.__CheckIdentifier(identifier,'motion'):
            return False
        data=self.__SendProtocol('GetMotion',[identifier])
        databytes=self._ToDataBytes(data)
        logging.info("dScriptBoard: %s: Motion Sensor %s is %s", self._HostName, identifier, self._OnOffStates[databytes[0]])
        self._throwEvent(self._HostName, 'motion', identifier, self._OnOffStates[databytes[0]])
        return self._OnOffStates[databytes[0]]

    '''Execute the GB, GetButton command and print the result into log'''
    def GetButton(self,identifier):
        logging.debug("dScriptBoard: GetButton: %s",[identifier])
        if not self._CustomFirmeware:
            return False
        if not self.__CheckIdentifier(identifier,'button'):
            return False
        data=self.__SendProtocol('GetButton',[identifier])
        databytes=self._ToDataBytes(data)
        logging.info("dScriptBoard: %s: Button %s was clicked %s times", self._HostName, identifier, databytes[0])
        self._throwEvent(self._HostName, 'button', identifier, databytes[0])
        return databytes[0]
		
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

