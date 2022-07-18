#!/usr/bin/env python
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import os
import sys
import logging as _LOGGER
import time

import asyncio

async def tcp_echo_client(message, loop): 
    try:
        _LOGGER.info("tcp_echo_client: running one shot client...")
        reader, writer = await asyncio.open_connection('127.0.0.1', 17123) 
        
        _LOGGER.debug("tcp_echo_client: Send: %s", message)
        writer.write(message.encode())

        _LOGGER.debug("tcp_echo_client: reading reply...")
        data = await reader.read(100)
        _LOGGER.info("tcp_echo_client: received: %s", data.decode())
        
        _LOGGER.debug("tcp_echo_client: end one shot client...")
        writer.close() 
    except Exception as e: 
        _LOGGER.debug("tcp_echo_client: exception: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)
              
def main():
    try:
        _LOGGER.info("main: starting program...")
        message = 'P' #ASCII P = decimal 80 = command: GetConfig 
        
        _LOGGER.debug("main: start asyncio loop")
        loop = asyncio.get_event_loop()    
        
        _LOGGER.debug("main: execute async echo client")
        loop.run_until_complete(tcp_echo_client(message, loop))

        _LOGGER.debug("main: close asyncio loop")
        loop.close()
        
        _LOGGER.debug("main: all done")
    except Exception as e: 
        _LOGGER.debug("main: Exception on main: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)

    _LOGGER.debug("main: exit now - BYE BYE")
    sys.exit()

#_LOGGER.basicConfig(format='%(levelname)s:%(message)s', level=_LOGGER.DEBUG)
_LOGGER.basicConfig(level=_LOGGER.DEBUG)
#_LOGGER.basicConfig(level=_LOGGER.INFO)
main()

