#!/usr/bin/env python
# version: 2020.06.22
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import sys
import logging as _LOGGER
import time
import random

def main():
    c=5
    
    _LOGGER.info("main: starting program...")
    from dScriptModule import dScriptVirtualBoard

    _LOGGER.debug("main: create dScriptVirtualBoard object")
    board = dScriptVirtualBoard()


#    _LOGGER.debug("main: showing board attributes")
#    for attr in dir(board):
#        if hasattr(board, attr ):
#            _LOGGER.debug("main: BOARD: %s = %s", attr, getattr(board, attr))

    time.sleep(2)
    board.ClickLightButton(1)
    time.sleep(2)

#    cmds = [ 'HeartBeat', 'GetConfig', 'GetLight', 'GetShutter', 'GetSocket', 'GetMotion', 'GetButton' ]
#    try:
#        i = 0
#        while i < c:
#            i += 1
#            
#            _LOGGER.info("main: executing %s random commands", c)
#            cmd = random.choice(list(cmds)) 
#            
#            _LOGGER.debug("main: execute: board.%s", cmd)
#            cmd_method = getattr(dScriptVirtualBoard, cmd)
#            cmd_method(board)
#            time.sleep(5)
#    except:
#        pass


    _LOGGER.debug("main: exit now - BYE BYE")
    sys.exit()

#_LOGGER.basicConfig(format='%(levelname)s:%(message)s', level=_LOGGER.DEBUG)
_LOGGER.basicConfig(level=_LOGGER.DEBUG)
#_LOGGER.basicConfig(level=_LOGGER.INFO)
main()
