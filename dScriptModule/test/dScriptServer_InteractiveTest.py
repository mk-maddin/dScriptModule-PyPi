#!/usr/bin/env python
# version: 2018.10.05
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import sys
import logging

def main():
    logging.info("main: starting program...")
    from dScriptModule import dScriptServer

    logging.debug("main: create dScriptServer object")
    try: 
        server = dScriptServer()
    except:
        logging.debug("main: using fallback definition")
        server = dScriptModule.dScriptServer()


    logging.debug("main: starting server")
    server.StartServer()

    logging.debug("main: sleeping until interrupt")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    logging.debug("main: keyboard interrupted")

    logging.debug("main: stopping server")
    server.StopServer()

    logging.debug("main: exit now - BYE BYE")
    sys.exit()

#logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)
main()
