#!/usr/bin/env python
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import sys
import logging as _LOGGER
import time

def main():
    _LOGGER.info("main: starting program...")
    from dScriptModule import dScriptBoard

    _LOGGER.info("main: create dScriptBoard object")
    dSBoard = dScriptBoard('192.168.13.120')
    #dSBoard.SetAESKey('12345678901234567890123456789012') # use default of 'This MUST be 32 characters long.'
    dSBoard.SetProtocol('binaryaes')

    _LOGGER.info("main: initialize dSBoard")
    dSBoard.InitBoard()
    time.sleep(1)

    ## Done during InitBoard()
    #_LOGGER.info("main: execute main GetXxxx functions")
    #dSBoard.GetStatus()
    #if dSBoard._CustomFirmeware:
    #    dSBoard.GetConfig() # methode exists only in custom firmware

    if not dSBoard._CustomFirmeware:   
        _LOGGER.info("main: execute %s SetRelay functions", dSBoard._VirtualRelays)
        i=0
        while i < dSBoard._VirtualRelays:
            i += 1
            _LOGGER.debug("main: test relay: %s", i)
            dSBoard.SetRelay(i,'on')
            time.sleep(2)
            #dSBoard.GetRelay(i)  #not implemented yet
            #time.sleep(1)
            dSBoard.SetRelay(i,'off')
            time.sleep(2)

    if dSBoard._CustomFirmeware:
        _LOGGER.info("main: execute %s SetLight functions", dSBoard._ConnectedLights)
        i=0
        while i < dSBoard._ConnectedLights:
            i += 1
            dSBoard.SetLight(i,'on')
            time.sleep(2)
            dSBoard.GetLight(i)
            time.sleep(1)
            dSBoard.SetLight(i,'off')
            time.sleep(2)
        
        _LOGGER.info("main: execute %s SetShutter functions", dSBoard._ConnectedShutters)
        i=0
        while i < dSBoard._ConnectedShutters:
            i += 1
            dSBoard.SetShutter(i,5)
            while not dSBoard.GetShutter(i)[0] == 5:
                _LOGGER.debug("main: wait for shutter to complete")
                time.sleep(5)
            dSBoard.SetShutter(i,'open')
            while dSBoard.GetShutter(i)[0] > 100:
                _LOGGER.debug("main: wait for shutter to complete")
                time.sleep(5)

        _LOGGER.info("main: execute %s SetSocket functions", dSBoard._ConnectedSockets)
        i=0
        while i < dSBoard._ConnectedSockets:
            i += 1
            dSBoard.SetSocket(i,'on')
            time.sleep(2)
            dSBoard.GetSocket(i)
            dSBoard.SetSocket(i,'off')
            time.sleep(2)

    _LOGGER.debug("main: exit now - BYE BYE")
    sys.exit()

_LOGGER.basicConfig(format='%(levelname)s:%(message)s', level=_LOGGER.DEBUG)
_LOGGER.basicConfig(level=_LOGGER.DEBUG)
#_LOGGER.basicConfig(level=_LOGGER.INFO)
main()
