#!/usr/bin/python
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: 
#   object being able to translate dScript (by robot-electronics / devantech ltd.) board commands
#   into the different protocols available by these boards

import logging
_LOGGER = logging.getLogger(__name__)

from bitstring import BitArray
from .dScriptEvent import *

class dScriptObject(object):

    IP = '127.0.0.1'
    Port = 17123

    _EventHandlers = { 'topic':[]}

    _Protocols = {1:'modbus', 2:'ascii', 3:'binary', 4:'binaryaes'}
    _DecimalCommands = {48:'GetStatus', 49:'SetRelay', 50:'SetOutput', 51:'GetRelay', 52:'GetInput', 53:'GetAnalogue', 54:'GetCounter', 
            64:'SetLight', 65:'SetShutter', 66:'SetSocket',
            80:'GetConfig', 81:'GetLight', 82:'GetShutter', 83:'GetSocket', 84:'GetMotion', 85:'GetButton', 
            0:'HeartBeat', 255:'TestOnline' , 254:'StopServer' , 253:'BoardRestart'}
    _BinaryCommands = {'\x30':'GetStatus', '\x31':'SetRelay', '\x32':'SetOutput', '\x33':'GetRelay', '\x34':'GetInput', '\x35':'GetAnalogue', '\x36':'GetCounter', 
            '\x40':'SetLight', '\x41':'SetShutter', '\x42':'SetSocket',
            '\x50':'GetConfig', '\x51':'GetLight', '\x52':'GetShutter', '\x53':'GetSocket', '\x54':'GetMotion', '\x55':'GetButton', 
            '\x00':'HeartBeat','\xff':'TestOnline', '\xfe':'StopServer', '\xfd':'BoardRestart'}
    _ASCIICommands = {'GS':'GetStatus', 'SR':'SetRelay', 'SO':'SetOutput', 'GR':'GetRelay', 'GI':'GetInput', 'GA':'GetAnalogue', 'GC':'GetCounter', 
            'SL':'SetLight', 'SH':'SetShutter', 'SC':'SetSocket',
            'GO':'GetConfig', 'GL':'GetLight', 'GH':'GetShutter', 'GK':'GetSocket', 'GM':'GetMotion', 'GB':'GetButton', 
            'HB':'HeartBeat', 'TO':'TestOnline' , 'SV':'StopServer', 'BR':'BoardRestart'}

    _AESNonceInitCMD = 48 # decimal code of the GetStatus command which sends an inital Nonce without requiring one
    _AESNonceCommands = [ 48, 49, 50, 64, 65, 66, 253 ] # commands which require AES Nonce

    _BinaryReturnByteCounts = {'GetStatus':8, 'SetRelay':1, 'SetOutput':1, 'GetRelay':5, 'GetInput':2, 'GetAnalogue':16, 'GetCounter':8, 
            'SetLight':1, 'SetShutter':1, 'SetSocket':1,
            'GetConfig':12, 'GetLight':1, 'GetShutter':2, 'GetSocket':1, 'GetMotion':1, 'GetButton':1,
            'HeartBeat':0, 'TestOnline':0, 'StopServer':0, 'BoardRestart':0}

    _Modules = {30:'dS3484', 31:'dS1242', 34:'dS2824', 35:'dS378'}
    _ModulesConfig = {30:{'_PhysicalRelays':4,}, 31:{'_PhyiscalRelays':2}, 34:{'_PhysicalRelays':24}, 35:{'_PhysicalRelays':8}}
    _OnOffStates = {0:'off', 1:'on', 2:'toggle'}
    _ShutterStates = {0:'stopped', 1:'opening', 2:'closing'}

    _Protocol = 'binary'
    _AESKey = 'This MUST be 32 characters long.'
    __AESKeyLenght = 32
    _Nonce = ''

    '''Check if element is within list'''
    def _IsInList(self, element, checklist):
        #_LOGGER.debug("dScriptObject: _IsInList")
        for i in checklist:
            if (i == element):
                return True
        return False

    '''Find the key to a dictionary value''' 
    def _GetKeyByValue(self, element, dictionary):
        #_LOGGER.debug("dScriptObject: _GetKeyByValue")
        for key,value in dictionary.items():
            if value == element:
                return key
        return None

    '''Translate received set of data into byte array'''
    def _ToDataBytes(self,data):
        #_LOGGER.debug("dScriptObject: _ToDataBytes: %s",data)
        databytes = list(data)
        _LOGGER.debug("dScriptBoard: received databytes: %s", databytes)
        return databytes

    '''Translate received set of data into bit array'''
    def _ToDataBits(self,data):
        #_LOGGER.debug("dScriptObject: _ToDataBits: %s",data)
        databits = (BitArray(bytes=data,offset=1)).bin
        _LOGGER.debug("dScriptObject: received databits: %s", databits)
        return databits

    def addEventHandler(self, topic, handler):
        #_LOGGER.debug("dScriptObject: addEventHandler")
        topic=topic.lower()
        if not self._IsInList(topic,self._EventHandlers.keys()):
            raise Exception("Unknown event handler topic: %s", topic)
            return False
        self._EventHandlers[topic].append(handler) 
        return True

    def removeEventHandler(self, topic, handler):
        #_LOGGER.debug("dScriptObject: removeEventHandler")
        topic=topic.lower()
        if not self._IsInList(topic,self._EventHandlers.keys()):
            raise Exception("Unknown event handler topic: %s", topic)
            return False
        self._EventHandlers[topic].remove(handler)
        return True

    def _throwEvent(self, sender=IP, topic='topic', identifier=None, value=None):
        _LOGGER.debug("dScriptObject: _throwEvent: from %s about %s for %s with value %s", sender, topic, identifier, value)
        topic=topic.lower()
        if not self._IsInList(topic,self._EventHandlers.keys()):
            raise Exception("Unknown event handler topic: %s", topic)
            return False
        
        eventobj = dScriptEventObj(sender,topic,identifier,value)
        for handler in self._EventHandlers[topic]:
            eventobj.event += handler
        #_LOGGER.debug("dScriptObject: _throwEvent: object: %s", eventobj)
        eventobj.throw()

    '''Print the status of this dScriptObject'''
    def PrintInfo(self):
        #_LOGGER.debug("dScriptObject: PrintInfo")
        for attr in dir(self):
            if hasattr( self, attr ):
                _LOGGER.info("dScriptObject: %s: %s = %s", self._HostName, attr, getattr(self, attr))

    '''Set the communication protocol used'''
    def SetProtocol(self, PROTOCOL='binary'):
        #_LOGGER.debug("dScriptObject: SetProtocol")
        PROTOCOL=PROTOCOL.lower()
        if not self._IsInList(PROTOCOL,self._Protocols.values()):
            raise Exception("%s is supported protocol",PROTOCOL)
            return False
        if PROTOCOL == self._Protocols[4] and not self._AESKey:
            raise Exception("AES is required for %s protocol - use SetAESKey first",PROTOCOL) 
            return False
        self._Protocol = PROTOCOL
        return True

    '''Set the AESKey used for BinaryAES communication protocol'''
    def SetAESKey(self, KEY):
        #_LOGGER.debug("dScriptObject: SetAESKey")
        if not len(KEY) == self.__AESKeyLenght:
            raise Exception("AES key must be exactly %s characters long", self.__AESKeyLenght)
            return False
        self._AESKey = KEY
        return True
