#!/usr/bin/env python
# version: 2020.06.14
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import os
import sys
import logging
import time

def main():
    logging.info("main: starting program...")
    import dScriptModule

    logging.debug("main: create dScriptServer object")
    server = dScriptModule.dScriptServer()
    
    i=0
    while i == 0:
        try:
            logging.debug("main: starting server")
            server.StartServer()
            logging.debug("main: sleeping 1 seconds") 
            time.sleep(1)
            logging.debug("main: stopping server")
            server.StopServer()    
            time.sleep(1)
        except Exception as e:
            logging.error("main: dscript server error: %s", str(e))
            i=1

    logging.debug("main: exit now - BYE BYE")
    sys.exit()

#logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)
main()

