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

    logging.debug("main: create dScriptBoard object")
    #board = dScriptBoard()
    board = dScriptBoard('192.168.13.120')

    logging.debug("main: execute main GetXxxx functions")
    board.GetStatus()
    board.GetConfig()
    board.PrintInfo()
   
    logging.debug("main: execute SetLight functions")
    board.SetLight(1,'on')
    board.GetLight(1)
    board.SetLight(1,'off')

    logging.debug("main: execute SetShutter functions")
    board.SetShutter(1,22)
    time.sleep(10)
    board.GetShutter(1)
    board.SetShutter(1,'open')
    time.sleep(10)

    logging.debug("main: exit now - BYE BYE")
    sys.exit()

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
main()
