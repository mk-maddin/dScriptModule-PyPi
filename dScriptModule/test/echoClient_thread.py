#!/usr/bin/env python
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import os
import sys
import logging as _LOGGER
import time

import threading
import socket

def create_echo_client():
    HOST = '127.0.0.1'  # The server's hostname or IP address
    PORT = 17123        # The port used by the server
    try:
        _LOGGER.info("tcp_echo_client: running one shot client...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(b'P') #ASCII P = decimal 80 = command: GetConfig 
            data = s.recv(100) 
        
        _LOGGER.info("create_echo_client: received: %s", repr(data))
    except Exception as e:
        _LOGGER.debug("create_echo_client: exception: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)
        
def main():
    try:
        _LOGGER.info("main: starting program...")
        threads = []    
        
        for i in range(50):
            _LOGGER.debug("main: prepare thread %s", i)
            thread = threading.Thread(target=create_echo_client)
            thread.start()
            threads.append(thread)

        _LOGGER.debug("main: join threads")
        for thread in threads:
            thread.join()
        
        _LOGGER.debug("main: all done")
    except Exception as e: 
        _LOGGER.debug("main: Exception on main: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)

    _LOGGER.debug("main: exit now - BYE BYE")
    sys.exit()

#_LOGGER.basicConfig(format='%(levelname)s:%(message)s', level=_LOGGER.DEBUG)
_LOGGER.basicConfig(level=_LOGGER.DEBUG)
#_LOGGER.basicConfig(level=_LOGGER.INFO)
main()

