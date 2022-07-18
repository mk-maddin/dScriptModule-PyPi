#!/usr/bin/python
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: 
#   object capturing all incoming command triggers (protocol independend) and trowing events

from __future__ import annotations
import logging
_LOGGER = logging.getLogger(__name__)

from .dScriptObject import *
import asyncio
import struct
import socket
from Crypto import Random
from Crypto.Cipher import AES

class dScriptBoard(dScriptObject):

    _HostName=None
    friendlyname=None
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
    __loop = None
    
    '''Initialize the dScriptBoard element with at least its IP and port to be able to connect later'''
    def __init__(self, TCP_IP, TCP_PORT=17123, PROTOCOL='binary') -> None:
        _LOGGER.debug("dScriptBoard - %s:%s: __init__", TCP_IP, TCP_PORT)
        self.IP = TCP_IP
        self.Port = TCP_PORT
        self.SetProtocol(PROTOCOL)
        self.GetHostName()

    '''Send command protocol independend'''
    def __SendProtocol(self,command,arguments):
        _LOGGER.debug("dScriptBoard - %s: SendProtocol: %s | %s", self.friendlyname, command, arguments)
        try:
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
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: SendProtocol failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            return False
            
    '''Send command protocol independend'''
    async def __async_SendProtocol(self,command,arguments):
        _LOGGER.debug("dScriptBoard - %s: async_SendProtocol: %s | %s", self.friendlyname, command, arguments)
        try:
            msg=struct.pack("B",self._GetKeyByValue(command,self._DecimalCommands))
            for a in arguments:
                msg = msg + struct.pack("B",a)
            if self._Protocol == self._Protocols[4] and self._IsInList(msg[0], self._AESNonceCommands):    #BinaryAES and command with NONCE
                msg = await self._async_AESEncrypt(msg)
                data = await self.__async_Send(msg,16) #BinaryAES commands always return 16 bytes
                data = await self._async_AESEncrypt(data,self._GetKeyByValue(command,self._DecimalCommands))
                return data[:self._BinaryReturnByteCounts[command]] # return only the number of bytes usually returend by Binary protocol
            elif self._Protocol == self._Protocols[3] or self._Protocol == self._Protocols[4]:    #Binary or BinaryAES but command without NONCE
                return await self.__async_Send(msg,self._BinaryReturnByteCounts[command])
            else:
                raise Exception("Protocol not implemented yet: %s", self._Protocol)         
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_SendProtocol failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            return False
            
    '''Encrypt a message using AES encryption'''
    def _AESEncrypt(self,msg):
        _LOGGER.debug("dScriptBoard - %s: AESEncrypt: %s", self.friendlyname, msg)
        try:
            while len(msg) < 12:
                msg = msg + struct.pack("B",0)
            _LOGGER.debug("dScriptBoard - %s: AESEncrypt: msg extended: %s", self.friendlyname, msg)
            if msg[0] == self._AESNonceInitCMD:
                _LOGGER.debug("dScriptBoard - %s: AESEncrypt: initialize Nonce command", self.friendlyname)
                msg = msg + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) # just add 0 for initalize
                self._Nonce = '' # reset nonce to prevent duplicate usage
            elif self._IsInList(msg[0], self._AESNonceCommands):
                _LOGGER.debug("dScriptBoard - %s: AESEncrypt: command requiring Nonce", self.friendlyname)
                if not self._Nonce:
                    _LOGGER.info("dScriptBoard - %s: AESEncrypt: need to (re)initiate Nonce value", self.friendlyname)
                    self.GetStatus()
                if not self._Nonce:
                    _LOGGER.error("dScriptBoard: %s: AESEncrypt: could not receive Nonce", self.friendlyname)
                    return False
                msg = msg + self._Nonce
                self._Nonce = '' # reset nonce to prevent duplicate usage
            else:
                _LOGGER.debug("dScriptBoard - %s: AESEncrypt: command not using Nonce", self.friendlyname)
                msg = msg + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) # just add 0 for unneeded
            _LOGGER.debug("dScriptBoard - %s: AESEncrypt: msg to encrypt: %s", self.friendlyname, msg)
            iv = Random.new().read(AES.block_size)
            cipher = AES.new(self._AESKey, AES.MODE_CBC, iv)
            msg = iv + cipher.encrypt(msg)
            _LOGGER.debug("dScriptBoard - %s: AESEncrypt: msg encrypted: %s", self.friendlyname, msg)
            return msg
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: AESEncrypt failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            return False     

    '''Encrypt a message using AES encryption'''
    async def _async_AESEncrypt(self,msg):
        _LOGGER.debug("dScriptBoard - %s: asnyc_AESEncrypt: %s", self.friendlyname, msg)
        try:
            while len(msg) < 12:
                msg = msg + struct.pack("B",0)
            _LOGGER.debug("dScriptBoard - %s: async_AESEncrypt: msg extended: %s", self.friendlyname, msg)
            if msg[0] == self._AESNonceInitCMD:
                _LOGGER.debug("dScriptBoard - %s: async_AESEncrypt: initialize Nonce command", self.friendlyname)
                msg = msg + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) # just add 0 for initalize
                self._Nonce = '' # reset nonce to prevent duplicate usage
            elif self._IsInList(msg[0], self._AESNonceCommands):
                _LOGGER.debug("dScriptBoard - %s: async_AESEncrypt: command requiring Nonce", self.friendlyname)
                if not self._Nonce:
                    _LOGGER.info("dScriptBoard - %s: async_AESEncrypt: need to (re)initiate Nonce value", self.friendlyname)
                    await self.async_GetStatus()
                if not self._Nonce:
                    _LOGGER.error("dScriptBoard: %s: async_AESEncrypt: could not receive Nonce", self.friendlyname)
                    return False
                msg = msg + self._Nonce
                self._Nonce = '' # reset nonce to prevent duplicate usage
            else:
                _LOGGER.debug("dScriptBoard - %s: async_AESEncrypt: command not using Nonce", self.friendlyname)
                msg = msg + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) + struct.pack("B",0) # just add 0 for unneeded
            _LOGGER.debug("dScriptBoard - %s: async_AESEncrypt: msg to encrypt: %s", self.friendlyname, msg)
            await asyncio.sleep(0)
            iv = Random.new().read(AES.block_size)
            cipher = AES.new(self._AESKey, AES.MODE_CBC, iv)
            msg = iv + cipher.encrypt(msg)
            _LOGGER.debug("dScriptBoard - %s: async_AESEncrypt: msg encrypted: %s", self.friendlyname, msg)
            return msg
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_AESEncrypt failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            return False

    '''Decrypt a message using AES encryption'''
    def _AESDecrypt(self,data,binaryid):
        _LOGGER.debug("dScriptBoard - %s: AESDecrypt: %s", self.friendlyname, data)
        try:
            cipher = AES.new(self._AESKey, AES.MODE_CBC, data[:AES.block_size])
            data = cipher.decrypt(data[AES.block_size:])
            if self._IsInList(binaryid, self._AESNonceCommands):
                _LOGGER.debug("dScriptBoard - %s: AESDecrypt: update Nonce value: %s", self.friendlyname, data[12:])
                self._Nonce = data[12:]
            _LOGGER.debug("dScriptBoard - %s: AESDecrypt: data decrypted: %s", self.friendlyname, data)
            return data
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: AESEncrypt failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            return False
            
    '''Decrypt a message using AES encryption'''
    async def _async_AESDecrypt(self,data,binaryid):
        _LOGGER.debug("dScriptBoard - %s: async_AESDecrypt: %s", self.friendlyname, data)
        try:
            cipher = AES.new(self._AESKey, AES.MODE_CBC, data[:AES.block_size])
            data = cipher.decrypt(data[AES.block_size:])
            await asyncio.sleep(0)
            if self._IsInList(binaryid, self._AESNonceCommands):
                _LOGGER.debug("dScriptBoard - %s: async_AESDecrypt: update Nonce value: %s", self.friendlyname, data[12:])
                self._Nonce = data[12:]
            _LOGGER.debug("dScriptBoard - %s: async_AESDecrypt: data decrypted: %s", self.friendlyname, data)
            return data
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_AESDecrypt failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            return False
        
    '''Send a message to the board''' 
    def __Send(self,msg,buff):
        _LOGGER.debug("dScriptBoard - %s: Send: %s | %s", self.friendlyname, msg, buff)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.ConnectionTimeout)
            s.connect((self.IP, self.Port))
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: Send failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            return False
        try:
            s.send(msg)
            data = s.recv(buff)
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: Send failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            s.close()
            return False
        s.close()
        return data

    '''Send a message to the board''' 
    async def __async_Send(self,msg,buff,retry=False):
        _LOGGER.debug("dScriptBoard - %s: async_Send: %s | %s", self.friendlyname, msg, buff)
        try:
            writer = None
            if self.__loop is not None:
                _LOGGER.warning("dScriptBoard - %s: async_Send loop parameter is no longer forwarded as of python 3.10", self.friendlyname )
            #reader, writer = await asyncio.open_connection(self.IP, self.Port, loop=self.__loop)
            reader, writer = await asyncio.open_connection(self.IP, self.Port)
            writer.write(msg)
            data = await reader.read(buff)
            writer.close()
            return data
        except TimeoutError as e:
            if not retry:
                _LOGGER.debug("dScriptBoard - %s: async_Send retry sending: %s | %s", self.friendlyname, msg, buff)
                if writer:
                    writer.close()
                await self.__async_Send(msg,buff,True)
            else:
                _LOGGER.error("dScriptBoard - %s: async_Send failed with retry: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
                if not write is None:
                    writer.close()
                return False
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_Send failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            if not write is None:
                writer.close()
            return False
        
    '''Check if identifier parameter is valid'''
    def __CheckIdentifier(self,identifier,idtype) -> bool:
        _LOGGER.debug("dScriptBoard - %s: CheckIdentifier: %s | %s", self.friendlyname, identifier, idtype)
        try:
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
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: CheckIdentifier failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            return False
        if identifier <= 0 or identifier > identifier2:
            raise Exception("Maximum connected %s is: %s", idtype, identifier2)
            return False
        return True
            
    '''Check if we could execute SetXxxx correctly'''
    def __CheckSet(self,returnbyte) -> bool:
        _LOGGER.debug("dScriptBoard - %s: __CheckSet", self.friendlyname)
        if not returnbyte == 0:
            raise Exception("Could not set value - return %s", returnbyte)
            return False
        return True

    '''Find the hostname of this device - using dns resolution - and write it as an attribute'''
    def GetHostName(self) -> None:
        _LOGGER.debug("dScriptBoard - %s:%s: GetHostName", self.IP, self.Port)
        try:
            name = socket.gethostbyaddr(self.IP)[0]
            if name:
                if name.split('.')[0] == '192':
                   self._HostName = name
                else:
                   self._HostName = name.split('.')[0]
            elif not self._HostName:
                self._HostName = self.IP
            self.friendlyname = self._HostName
            _LOGGER.info("dScriptBoard - %s:%s: HostName is now: %s (friendlyname: %s)", self.IP, self.Port, self._HostName, self.friendlyname)
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s:%s: GetHostName failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)

    '''Initialize the board and write its results as attributes'''
    def InitBoard(self) -> None:
        _LOGGER.debug("dScriptBoard - %s: InitBoard", self.friendlyname)
        self.GetHostName()
        self.GetStatus()
        self.GetConfig()

    '''Initialize the board and write its results as attributes'''
    async def async_InitBoard(self) -> None:
        _LOGGER.debug("dScriptBoard - %s: async_InitBoard", self.friendlyname)
        self.GetHostName()
        await self.async_GetStatus()
        await self.async_GetConfig()
        
    '''Execute the GS, GetStatus command on the board and write its results as attributes'''
    def GetStatus(self) -> None:
        _LOGGER.debug("dScriptBoard - %s: GetStatus", self.friendlyname)
        try:
            data=self.__SendProtocol('GetStatus',[])
            if isinstance(data, bool) or data is None:
                _LOGGER.debug("dScriptBoard - %s: GetStatus: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            databits=self._ToDataBits(data)

            _LOGGER.info("dScriptBoard - %s: GetStatus: update board status information", self.friendlyname)
            self._ModuleID=self._Modules[databytes[0]]
            self._SystemFirmwareMajor=databytes[1]
            self._SystemFirmwareMinor=databytes[2]
            self._ApplicationFirmwareMajor=databytes[3]
            self._ApplicationFirmwareMinor=databytes[4]
            self._Volts=float(databytes[5])/10.00
            self._Temperature=float(int(databits[(6*8):(8*8)],2)/10.00)
            self._throwEvent(self._HostName, 'status')
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: GetStatus failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            
    '''Execute the GS, GetStatus command on the board and write its results as attributes'''
    async def async_GetStatus(self) -> None:
        _LOGGER.debug("dScriptBoard - %s: async_GetStatus", self.friendlyname)
        try:
            data=await self.__async_SendProtocol('GetStatus',[])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: async_GetStatus: no informational result: %s", self.friendlyname, data)
                return None 
            databytes=self._ToDataBytes(data)
            databits=self._ToDataBits(data)

            _LOGGER.info("dScriptBoard - %s: async_GetStatus: update board status information", self.friendlyname)
            self._ModuleID=self._Modules[databytes[0]]
            self._SystemFirmwareMajor=databytes[1]
            self._SystemFirmwareMinor=databytes[2]
            self._ApplicationFirmwareMajor=databytes[3]
            self._ApplicationFirmwareMinor=databytes[4]
            self._Volts=float(databytes[5])/10.00
            self._Temperature=float(int(databits[(6*8):(8*8)],2)/10.00)
            self._throwEvent(self._HostName, 'status')
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_GetStatus failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            
    '''Execute the GC, GetConfig command on the board and write its results as attributes'''
    def GetConfig(self) -> None:
        _LOGGER.debug("dScriptBoard - %s: GetConfig", self.friendlyname)
        try:
            data=self.__SendProtocol('GetConfig',[])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: GetConfig: no informational result: %s", self.friendlyname, data)
                return None
        except:
            data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # on BinaryAES all data returned is 0 (so emulate bad return here)
        try:
            if data[6] == 0: # data[6] is the number of physical arrays - this should never be 0
                _LOGGER.info("dScriptBoard - %s: GetConfig: contains default firmware", self.friendlyname)
                self._CustomFirmeware=False
                return None
            self._CustomFirmeware=True
            databytes=self._ToDataBytes(data)

            _LOGGER.info("dScriptBoard - %s: GetConfig: update board config information", self.friendlyname)
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
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_GetConfig failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
        
    '''Execute the GC, GetConfig command on the board and write its results as attributes'''
    async def async_GetConfig(self) -> None:
        _LOGGER.debug("dScriptBoard - %s: async_GetConfig", self.friendlyname)
        try:
            data=await self.__async_SendProtocol('GetConfig',[])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: async_GetConfig: no informational result: %s", self.friendlyname, data)
                return None
        except:
            data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # on BinaryAES all data returned is 0 (so emulate bad return here)
        try:
            if data[6] == 0: # data[6] is the number of physical arrays - this should never be 0
                _LOGGER.info("dScriptBoard - %s: GetConfig: contains default firmware", self.friendlyname)
                self._CustomFirmeware=False
                return None
            self._CustomFirmeware=True
            databytes=self._ToDataBytes(data)

            _LOGGER.info("dScriptBoard - %s: async_GetConfig: update board config information", self.friendlyname)
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
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_GetConfig failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            
    '''Execute the GL, GetLight command and print the result into log'''
    def GetLight(self,identifier) -> None | str:
        _LOGGER.debug("dScriptBoard - %s: GetLight: %s", self.friendlyname, identifier)
        try:
            if not self._CustomFirmeware:
                return None
            if not self.__CheckIdentifier(identifier,'light'):
                return None
            data=self.__SendProtocol('GetLight', [identifier])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: GetLight: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            _LOGGER.info("dScriptBoard - %s: GetLight: Light %s is %s", self.friendlyname, identifier, self._OnOffStates[databytes[0]])
            self._throwEvent(self._HostName, 'light', identifier, self._OnOffStates[databytes[0]])
            return self._OnOffStates[databytes[0]]
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: GetLight failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            
    '''Execute the GL, GetLight command and print the result into log'''
    async def async_GetLight(self,identifier) -> None | str:
        _LOGGER.debug("dScriptBoard - %s: async_GetLight: %s", self.friendlyname, identifier)
        try:
            if not self._CustomFirmeware:
                return None
            if not self.__CheckIdentifier(identifier,'light'):
                return None
            data=await self.__async_SendProtocol('GetLight', [identifier])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: async_GetLight: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            _LOGGER.info("dScriptBoard - %s: async_GetLight: Light %s is %s", self.friendlyname, identifier, self._OnOffStates[databytes[0]])
            self._throwEvent(self._HostName, 'light', identifier, self._OnOffStates[databytes[0]])
            return self._OnOffStates[databytes[0]]
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_GetLight failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
        
    '''Execute the GH, GetShutter command and print the result into log'''
    def GetShutter(self,identifier) -> None | list:
        _LOGGER.debug("dScriptBoard - %s: GetShutter: %s", self.friendlyname, identifier)
        try:
            if not self._CustomFirmeware:
                return None
            if not self.__CheckIdentifier(identifier, 'shutter'):
                return None
            data=self.__SendProtocol('GetShutter', [identifier])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: GetShutter: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            _LOGGER.info("dScriptBoard - %s: GetShutter: Shutter %s is %s at level %s%%", self.friendlyname, identifier, self._ShutterStates[databytes[1]], databytes[0])
            self._throwEvent(self._HostName, 'shutter', identifier, databytes[0])
            return [databytes[0],self._ShutterStates[databytes[1]]]
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: GetShutter failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
            
    '''Execute the GH, GetShutter command and print the result into log'''
    async def async_GetShutter(self,identifier) -> None | list:
        _LOGGER.debug("dScriptBoard - %s: async_GetShutter: %s", self.friendlyname, identifier)
        try:
            if not self._CustomFirmeware:
                return None
            if not self.__CheckIdentifier(identifier,'shutter'):
                return None
            data=await self.__async_SendProtocol('GetShutter', [identifier])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: async_GetShutter: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            _LOGGER.info("dScriptBoard - %s: async_GetShutter: Shutter %s is %s at level %s%%", self.friendlyname, identifier, self._ShutterStates[databytes[1]], databytes[0])
            self._throwEvent(self._HostName, 'shutter', identifier, databytes[0])
            return [databytes[0],self._ShutterStates[databytes[1]]]
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_GetShutter failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)        
        
    '''Execute the GC, GetSocket command and print the result into log'''
    def GetSocket(self,identifier) -> None | str:
        _LOGGER.debug("dScriptBoard - %s: GetSocket: %s", self.friendlyname, identifier)
        try:
            if not self._CustomFirmeware:
                return None
            if not self.__CheckIdentifier(identifier,'socket'):
                return None
            data=self.__SendProtocol('GetSocket', [identifier])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: GetSocket: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            _LOGGER.info("dScriptBoard - %s: GetSocket: Socket %s is %s", self.friendlyname, identifier, self._OnOffStates[databytes[0]])
            self._throwEvent(self._HostName, 'socket', identifier, self._OnOffStates[databytes[0]])
            return self._OnOffStates[databytes[0]]
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: GetSocket failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)   
            
    '''Execute the GC, GetSocket command and return the result'''
    async def async_GetSocket(self,identifier) -> None | str:
        _LOGGER.debug("dScriptBoard - %s: async_GetSocket: %s", self.friendlyname, identifier)
        try:
            if not self._CustomFirmeware:
                return None
            if not self.__CheckIdentifier(identifier,'socket'):
                return None
            data=await self.__async_SendProtocol('GetSocket', [identifier])
            if isinstance(data, bool) or data is None:
                _LOGGER.debug("dScriptBoard - %s: async_GetSocket: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            _LOGGER.info("dScriptBoard - %s: async_GetSocket: Socket %s is %s", self.friendlyname, identifier, self._OnOffStates[databytes[0]])
            self._throwEvent(self._HostName, 'socket', identifier, self._OnOffStates[databytes[0]])
            return self._OnOffStates[databytes[0]]
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_GetSocket failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)       
    
    '''Execute the GM, GetMotion command and return the result'''
    def GetMotion(self,identifier) -> None | str:
        _LOGGER.debug("dScriptBoard - %s: GetMotion: %s", self.friendlyname, identifier)
        try:
            if not self._CustomFirmeware:
                return None
            if not self.__CheckIdentifier(identifier,'motion'):
                return None
            data=self.__SendProtocol('GetMotion', [identifier])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: GetMotion: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            _LOGGER.info("dScriptBoard - %s: GetMotion: Motion Sensor %s is %s", self.friendlyname, identifier, self._OnOffStates[databytes[0]])
            self._throwEvent(self._HostName, 'motion', identifier, self._OnOffStates[databytes[0]])
            return self._OnOffStates[databytes[0]]
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: GetMotion failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)  

    '''Execute the GM, GetMotion command and return the result'''
    async def async_GetMotion(self,identifier) -> None | str:
        _LOGGER.debug("dScriptBoard - %s: async_GetMotion: %s", self.friendlyname, identifier)
        try:
            if not self._CustomFirmeware:
                return None
            if not self.__CheckIdentifier(identifier,'motion'):
                return None
            data=await self.__async_SendProtocol('GetMotion', [identifier])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: async_GetMotion: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            _LOGGER.info("dScriptBoard - %s: async_GetMotion: Motion Sensor %s is %s", self.friendlyname, identifier, self._OnOffStates[databytes[0]])
            self._throwEvent(self._HostName, 'motion', identifier, self._OnOffStates[databytes[0]])
            return self._OnOffStates[databytes[0]]
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: async_GetMotion failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)              
            
    '''Execute the GB, GetButton command and return the result'''
    def GetButton(self,identifier) -> None | int:
        _LOGGER.debug("dScriptBoard - %s: GetButton: %s", self.friendlyname, identifier)
        try:
            if not self._CustomFirmeware:
                return None
            if not self.__CheckIdentifier(identifier,'button'):
                return None
            data=self.__SendProtocol('GetButton', [identifier])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: GetButton: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            _LOGGER.info("dScriptBoard - %s: GetButton: Button %s was clicked %s times", self.friendlyname, identifier, databytes[0])
            self._throwEvent(self._HostName, 'button', identifier, databytes[0])
            return databytes[0]
        except Exception as e: 
            _LOGGER.error("dScriptBoard - %s: GetButton failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)              

    '''Execute the GB, GetButton command and return the result'''
    async def async_GetButton(self,identifier) -> None | int:
        _LOGGER.debug("dScriptBoard - %s: async_GetButton: %s", self.friendlyname, identifier)
        try:
            if not self._CustomFirmeware:
                return None
            if not self.__CheckIdentifier(identifier,'button'):
                return None
            data=await self.__async_SendProtocol('GetButton', [identifier])
            if isinstance(data, bool) or data is None:    
                _LOGGER.debug("dScriptBoard - %s: async_GetButton: no informational result: %s", self.friendlyname, data)
                return None
            databytes=self._ToDataBytes(data)
            _LOGGER.info("dScriptBoard - %s: async_GetButton: Button %s was clicked %s times", self.friendlyname, identifier, databytes[0])
            self._throwEvent(self._HostName, 'button', identifier, databytes[0])
            return databytes[0]
        except Exception as e:
            _LOGGER.error("dScriptBoard - %s: async_GetButton failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)

    '''Execute the SR, SetRelay command to define a relay status'''
    def SetRelay(self,identifier,state) -> None | bool:
        _LOGGER.debug("dScriptBoard - %s: SetRelay: %s | %s", self.friendlyname, identifier, state)
        try:
            if not self.__CheckIdentifier(identifier,'relay'):
                return None
            data=self.__SendProtocol('SetRelay',[identifier,self._GetKeyByValue(state.lower(),self._OnOffStates)])
            databytes=self._ToDataBytes(data)
            return self.__CheckSet(self._ToDataBytes(data)[0])
        except Exception as e:
            _LOGGER.error("dScriptBoard - %s: SetRelay failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)

    '''Execute the SR, SetRelay command to define a relay status'''
    async def async_SetRelay(self,identifier,state) -> None | bool:
        _LOGGER.debug("dScriptBoard - %s: async_SetRelay: %s | %s", self.friendlyname, identifier, state)
        try:
            if not self.__CheckIdentifier(identifier,'relay'):
                return None
            data=await self.__async_SendProtocol('SetRelay',[identifier,self._GetKeyByValue(state.lower(),self._OnOffStates)])
            databytes=self._ToDataBytes(data)
            return self.__CheckSet(self._ToDataBytes(data)[0])
        except Exception as e:
            _LOGGER.error("dScriptBoard - %s: async_SetRelay failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)

    '''Execute the SL, SetLight command to define a light status'''
    def SetLight(self,identifier,state) -> None | bool:
        _LOGGER.debug("dScriptBoard - %s: SetLight: %s | %s", self.friendlyname, identifier, state)
        try:
            if not self._CustomFirmeware: # fallback to legacy relay action
                return self.SetRelay(identifier,state)
            if not self.__CheckIdentifier(identifier,'light'):
                return None
            data=self.__SendProtocol('SetLight',[identifier,self._GetKeyByValue(state.lower(),self._OnOffStates)])
            databytes=self._ToDataBytes(data)
            return self.__CheckSet(self._ToDataBytes(data)[0])
        except Exception as e:
            _LOGGER.error("dScriptBoard - %s: SetLight failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)

    '''Execute the SL, SetLight command to define a light status'''
    async def async_SetLight(self,identifier,state) -> None | bool:
        _LOGGER.debug("dScriptBoard - %s: async_SetLight: %s | %s", self.friendlyname, identifier, state)
        try:
            if not self._CustomFirmeware: # fallback to legacy relay action
                return await self.async_SetRelay(identifier,state)
            if not self.__CheckIdentifier(identifier,'light'):
                return None
            data=await self.__async_SendProtocol('SetLight',[identifier,self._GetKeyByValue(state.lower(),self._OnOffStates)])
            databytes=self._ToDataBytes(data)
            return self.__CheckSet(self._ToDataBytes(data)[0])
        except Exception as e:
            _LOGGER.error("dScriptBoard - %s: async_SetLight failed: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)

    '''Execute the SH, SetShutter command to define a shutter status'''
    def SetShutter(self,identifier,state) -> None | bool:
        _LOGGER.debug("dScriptBoard - %s: SetShutter: %s | %s", self.friendlyname, identifier, state)
        try:
            if not self._CustomFirmeware: # fallback to legacy relay action
                return self.SetRelay(identifier,state)
            if not self.__CheckIdentifier(identifier,'shutter'):
                return None
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
        except Exception as e:
            _LOGGER.error("dScriptBoard - %s: SetShutter failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)

    '''Execute the SH, SetShutter command to define a shutter status'''
    async def async_SetShutter(self,identifier,state) -> None | bool:
        _LOGGER.debug("dScriptBoard - %s: async_SetShutter: %s | %s", self.friendlyname, identifier, state)
        try:
            if not self._CustomFirmeware: # fallback to legacy relay action
                return await self.async_SetRelay(identifier,state)
            if not self.__CheckIdentifier(identifier,'shutter'):
                return None
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
            data=await self.__async_SendProtocol('SetShutter',[identifier,state])
            databytes=self._ToDataBytes(data)
            return self.__CheckSet(self._ToDataBytes(data)[0])
        except Exception as e:
            _LOGGER.error("dScriptBoard - %s: async_SetShutter failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)

    '''Execute the SC, SetSocket command to define a socket status'''
    def SetSocket(self,identifier,state) -> None | bool:
        _LOGGER.debug("dScriptBoard - %s: SetSocket: %s | %s", self.friendlyname, identifier, state)
        try:
            if not self._CustomFirmeware: # fallback to legacy relay action
                return self.SetRelay(identifier,state)
            if not self.__CheckIdentifier(identifier,'socket'):
                return None
            data=self.__SendProtocol('SetSocket',[identifier,self._GetKeyByValue(state.lower(),self._OnOffStates)])
            databytes=self._ToDataBytes(data)
            return self.__CheckSet(self._ToDataBytes(data)[0])
        except Exception as e:
            _LOGGER.error("dScriptBoard - %s: SetSocket failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)

    '''Execute the SC, SetSocket command to define a socket status'''
    async def async_SetSocket(self,identifier,state) -> None | bool:
        _LOGGER.debug("dScriptBoard - %s: async_SetSocket: %s | %s", self.friendlyname, identifier, state)
        try:
            if not self._CustomFirmeware: # fallback to legacy relay action
                return await self.async_SetRelay(identifier,state)
            if not self.__CheckIdentifier(identifier,'socket'):
                return None
            data=await self.__async_SendProtocol('SetSocket',[identifier,self._GetKeyByValue(state.lower(),self._OnOffStates)])
            databytes=self._ToDataBytes(data)
            return self.__CheckSet(self._ToDataBytes(data)[0])
        except Exception as e:
            _LOGGER.error("dScriptBoard - %s: async_SetSocket failed: %s (%s.%s)", self.friendlyname, str(e), e.__class__.__module__, type(e).__name__)
