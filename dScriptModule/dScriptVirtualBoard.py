#!/usr/bin/python
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: 
#   object capturing all incoming command triggers (protocol independend) and trowing events

###########!! WORK IN PROGRESS!!###########

import logging
_LOGGER = logging.getLogger(__name__)

from .dScriptBoard import *
import _thread
import time
import random

class dScriptVirtualBoard(dScriptBoard):

    '''Initialize the virtual dScriptBoard element'''
    def __init__(self, TCP_IP='127.0.0.1', TCP_PORT=17123, PROTOCOL='binary'):
        _LOGGER.debug("dScriptVirtualBoard: __init__")
        self._MACAddress="02:00:00:%02x:%02x:%02x" % (random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))
        self._ModuleID=random.choice(list(dScriptObject._Modules.keys()))
        self._CustomFirmeware=True
        self.InitBoard()

        self.dScriptServer = TCP_IP
        self.dScriptServer_Port = TCP_PORT
        self.SetProtocol(PROTOCOL)

        _thread.start_new_thread(self.__dScriptServerContacter,())

    '''Define board model such as connected relays lights shutters sockets etc'''
    def InitBoard(self):
        _LOGGER.debug("dScriptVirtualBoard: __initBoardConfig")
        self._PhysicalRelays = dScriptObject._ModulesConfig[self._ModuleID]['_PhysicalRelays']
        if self._PhysicalRelays == 2:
            self._ConnectedLights = 1
            self._ConnectedShutters = 0
            self._ConnectedSockets = 1
            self._ConnectedMotionSensors=1
            self._ConnectedButtons=2
        elif self._PhysicalRelays == 4:
            self._ConnectedLights = 1
            self._ConnectedShutters = 1
            self._ConnectedSockets = 1
            self._ConnectedMotionSensors=1
            self._ConnectedButtons=1
        elif self._PhysicalRelays == 8:
            self._ConnectedLights = 2
            self._ConnectedShutters = 2
            self._ConnectedSockets = 2
            self._ConnectedMotionSensors=1
            self._ConnectedButtons=1
        elif self._PhysicalRelays == 24:
            self._ConnectedLights = 2
            self._ConnectedShutters = 4
            self._ConnectedSockets = 12
            self._ConnectedMotionSensors=1
            self._ConnectedButtons=1
        self._initStates()
    
    '''Set the default state of board elements'''
    def _initStates(self):
        _LOGGER.debug("dScriptVirtualBoard: _initStates")
        #self._statesRelays = [0] * self._VirtualRelays
        self._statesLights = [0] * self._ConnectedLights
        self._statesSockets = [1] * self._ConnectedSockets #sockets are ON by default
        self._statesMotionSensors = [0] * self._ConnectedMotionSensors
        self._statesButtons = [0] * self._ConnectedButtons
  
        i=0
        self._statesShutters = [0] * self._ConnectedShutters
        self._closingTimeShutters = [0] * self._ConnectedShutters
        self._movementShutters = [0] * self._ConnectedShutters
        while i < self._ConnectedShutters:
            self._statesShutters[i] = random.randint(0, 100) #random closing level
            self._closingTimeShutters[i] = random.randint(225, 611)/10 #random closing time (in seconds - more or less realistic values)
            self._movementShutters[i] = self._GetKeyByValue('stopped',self._ShutterStates) # all shutters stopped after startup
            i=i+1

    '''dScriptServerContacter thread equally to dScriptRoomControl implementation'''
    def __dScriptServerContacter(self):
        _LOGGER.debug("dScriptVirtualBoard: __dScriptServerContacter")
        while True:
           self._HeartBeat()
           time.sleep(300)

    '''Send heartbeat to the dScriptServer'''
    def _HeartBeat(self):
        _LOGGER.debug("dScriptVirtualBoard: HeartBeat")
        data=self._dScriptBoard__SendProtocol('HeartBeat',[])
        databytes=self._ToDataBytes(data)
        _LOGGER.debug("dScriptVirtualBoard: HeartBeat: databytes received: %s", databytes)

    def GetHostName(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: GetHostName: Disabled")

#    def InitBoard(*args, **kwargs):
#        _LOGGER.debug("dScriptVirtualBoard: InitBoard: Disabled")

    def GetStatus(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: GetStatus: Disabled")

    def GetConfig(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: GetConfig: Disabled")

    def GetRelay(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: GetRelay: Disabled")

    def GetLight(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: GetLight: Disabled")

    def GetShutter(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: GetShutter: Disabled")

    def GetSocket(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: GetSocket: Disabled")

    def GetMotion(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: GetMotion: Disabled")

    def GetButton(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: GetButton: Disabled")

    def SetRelay(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: SetRelay: Disabled")

    def SetLight(self,identifier,state):
        _LOGGER.debug("dScriptVirtualBoard: SetLight: %s | %s",identifier,state)
        if not self._dScriptBoard__CheckIdentifier(identifier,'light'):
            return False
        try:
            s = self._GetKeyByValue(state.lower(),self._OnOffStates)
        except Exception as e: 
            _LOGGER.error("dScriptVirtualBoard: SetLight: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)
            return False
        if s == None:
            _LOGGER.error("dScriptVirtualBoard: SetLight: failed setting light %s - invalid state '%s' resolves to %s", identifier, state, s)
            return False

        if s == 2:
            if self._statesLights[identifier-1] == 0:
                self._statesLights[identifier-1] = 1
            elif self._statesLights[identifier-1] == 1:
                self._statesLights[identifier-1] = 2
        else:
            self._statesLights[identifier-1] = s
        _LOGGER.info("dScriptVirtualBoard: SetLight: light %s turned %s", identifier, self._OnOffStates[self._statesLights[identifier-1]])

        data=self._dScriptBoard__SendProtocol('GetLight',[identifier])
        databytes=self._ToDataBytes(data)
        _LOGGER.debug("dScriptVirtualBoard: SetLight: databytes received: %s", databytes)
        return data

    def SetShutter(self,identifier,state):
        _LOGGER.debug("dScriptVirtualBoard: SetShutter: %s | %s",identifier,state)        
        if not self._dScriptBoard__CheckIdentifier(identifier,'shutter'):
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
        else:
            _LOGGER.error("dScriptVirtualBoard: SetShutter: failed setting shutter %s - invalid state '%s'", identifier, state)
            return False

        data=self._dScriptBoard__SendProtocol('GetShutter',[identifier])
        databytes=self._ToDataBytes(data)
        _LOGGER.debug("dScriptVirtualBoard: SetShutter: databytes received: %s", databytes)
        return data

    def SetSocket(*args, **kwargs):
        _LOGGER.debug("dScriptVirtualBoard: SetSocket: Disabled")

    '''Virtually click a Light IO Button'''
    def ClickLightButton(self, identifier):
        _LOGGER.debug("dScriptVirtualBoard: PressLightButton")
        if not self._CustomFirmeware: # fallback to legacy relay action
            return self.SetRelay(identifier,state)
        return self.SetLight(identifier,'toggle')

    '''Virtually click a Shutter IO Button'''
    def ClickShutterButton(self, identifier):
        _LOGGER.debug("dScriptVirtualBoard: ClickShutterButton")
        if not self._CustomFirmeware: # fallback to legacy relay action
            return self.SetRelay(identifier,state)
        return self.SetLight(identifier,'toggle')

