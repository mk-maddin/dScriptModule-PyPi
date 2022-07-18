#!/usr/bin/env python
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import os
import sys
import logging as _LOGGER
import time

def main():
    try:
        _LOGGER.info("main: starting program...")
        import dScriptModule

        
        _LOGGER.debug("main: create dScriptServer object")
        server = dScriptModule.dScriptServer(TCP_IP='0.0.0.0')
        
        _LOGGER.debug("main: starting server")
        server.StartServer_async()    
    
        _LOGGER.debug("main: sleep...")
        while True:
            time.sleep(10)
            _LOGGER.debug("main: sleep 10 ...")
       
        _LOGGER.debug("main: stopping server")
        server.StopServer_async()
        
        _LOGGER.debug("main: all done")
    except KeyboardInterrupt:
        _LOGGER.debug("main: keyboard interrupted - stopping server")
        server.StopServer_async()
    except Exception as e: 
        _LOGGER.debug("main: Exception on main: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)

    _LOGGER.debug("main: exit now - BYE BYE")
    sys.exit()

#_LOGGER.basicConfig(format='%(levelname)s:%(message)s', level=_LOGGER.DEBUG)
_LOGGER.basicConfig(level=_LOGGER.DEBUG)
#_LOGGER.basicConfig(level=_LOGGER.INFO)
main()

