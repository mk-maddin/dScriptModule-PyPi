#!/usr/bin/env python
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import os
import sys
import logging as _LOGGER
import time

import asyncio

async def main_async():
    try:
        _LOGGER.info("main_async: starting ...")
        import dScriptModule
        
        _LOGGER.debug("main_async: create dScriptServer object")
        server = dScriptModule.dScriptServer()
        
        _LOGGER.debug("main: starting server")
        await server.async_StartServer()    
    
        _LOGGER.debug("main_async: sleep...")
        while True:
            await asyncio.sleep(10)
            _LOGGER.debug("main_async: sleep 10 ...")
        #await asyncio.sleep(10)
       
        _LOGGER.debug("main_async: stopping server")
        await server.async_StopServer()
        
        _LOGGER.debug("main_async: all done")
    except KeyboardInterrupt:
        _LOGGER.debug("main_async: keyboard interrupted - stopping server")
        await server.async_StopServer()
    except Exception as e: 
        _LOGGER.debug("main_async: Exception on main_async: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)

def main():
    try:
        _LOGGER.info("main: starting program...")
        
        _LOGGER.debug("main: startig async part...")
        asyncio.run(main_async())
        
        _LOGGER.debug("main: all done")
    except Exception as e: 
        _LOGGER.debug("main: Exception on main: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)

    _LOGGER.debug("main: exit now - BYE BYE")
    sys.exit()

#_LOGGER.basicConfig(format='%(levelname)s:%(message)s', level=_LOGGER.DEBUG)
_LOGGER.basicConfig(level=_LOGGER.DEBUG)
#_LOGGER.basicConfig(level=_LOGGER.INFO)
main()

