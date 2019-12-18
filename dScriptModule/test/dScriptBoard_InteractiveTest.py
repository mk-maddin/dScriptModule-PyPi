#!/usr/bin/env python
# version: 2018.10.05
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import sys
import logging
import time

def main():
    logging.info("main: starting program...")
    from dScriptModule import dScriptBoard

    logging.info("main: create dScriptBoard object")
    #board = dScriptBoard()
    board = dScriptBoard('192.168.13.120')

    logging.info("main: initialize board")
    board.InitBoard()

    ## Done during InitBoard()
    #logging.info("main: execute main GetXxxx functions")
    #board.GetStatus()
    #if board._CustomFirmeware:
    #    board.GetConfig() # methode exists only in custom firmware

    if not board._CustomFirmeware:   
        logging.info("main: execute %s SetRelay functions", board._VirtualRelays)
        i=0
        while i < board._VirtualRelays:
            i += 1
            board.SetRelay(i,'on')
            time.sleep(1)
            #board.GetRelay(i)  #not implemented yet
            board.SetRelay(i,'off')

    if board._CustomFirmeware:
        logging.info("main: execute %s SetLight functions", board._ConnectedLights)
        i=0
        while i < board._ConnectedLights:
            i += 1
            board.SetLight(i,'on')
            time.sleep(i)
            board.GetLight(i)
            board.SetLight(i,'off')
        
        logging.info("main: execute %s SetShutter functions", board._ConnectedShutters)
        i=0
        while i < board._ConnectedShutters:
            i += 1
            board.SetShutter(i,5)
            while not board.GetShutter(i) == 5:
                logging.debug("main: wait for shutter to complete")
                time.sleep(2)
            board.SetShutter(i,'open')
            while board.GetShutter(i) > 0:
                logging.debug("main: wait for shutter to complete")
                time.sleep(2)

        logging.info("main: execute %s SetSocket functions", board._ConnectedSockets)
        i=0
        while i < board._ConnectedSockets:
            i += 1
            board.SetSocket(i,'on')
            time.sleep(i)
            board.GetSocket(i)
            board.SetSocket(i,'off')

    logging.debug("main: exit now - BYE BYE")
    sys.exit()

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)
main()
