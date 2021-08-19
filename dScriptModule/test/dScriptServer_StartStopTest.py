#!/usr/bin/env python
# version: 2020.06.14
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import os
import sys
import logging as _LOGGER
import time

def main():
    _LOGGER.info("main: starting program...")
    import dScriptModule

    _LOGGER.debug("main: create dScriptServer object")
    server = dScriptModule.dScriptServer()
    
    i=0
    while i == 0:
        try:
            _LOGGER.debug("main: starting server")
            server.StartServer()
            _LOGGER.debug("main: sleeping 1 seconds") 
            time.sleep(1)
            _LOGGER.debug("main: stopping server")
            server.StopServer()    
            time.sleep(1)
        except Exception as e:
            _LOGGER.error("main: dscript server error: %s", str(e))
            i=1

    _LOGGER.debug("main: exit now - BYE BYE")
    sys.exit()

#_LOGGER.basicConfig(format='%(levelname)s:%(message)s', level=_LOGGER.DEBUG)
_LOGGER.basicConfig(level=_LOGGER.DEBUG)
#_LOGGER.basicConfig(level=_LOGGER.INFO)
main()

