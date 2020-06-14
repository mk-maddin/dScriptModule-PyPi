#!/usr/bin/env python
# version: 2020.06.14
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import sys
import logging
import time

def handler(sender, earg):
    logging.info("handler: executed")

    #logging.debug("handler: showing sender attributes")
    for attr in dir(sender):
        if hasattr(sender, attr ):
                logging.debug("handler: SENDER: %s = %s", attr, getattr(sender, attr))

    #logging.debug("handler: showing earg attributes")
    for attr in dir(earg):
        if hasattr(earg, attr ):
                logging.debug("handler: EARG: %s = %s", attr, getattr(earg, attr))


def main():
    logging.info("main: starting program...")
    from dScriptModule import dScriptServer

    logging.debug("main: create dScriptServer object")
    server = dScriptServer()

    logging.debug("main: starting server")
    server.StartServer()

    logging.debug("main: register handler")
    server.addEventHandler('heartbeat',handler)
    server.addEventHandler('getstatus',handler)
    server.addEventHandler('getconfig',handler)
    server.addEventHandler('getlight',handler)
    server.addEventHandler('getshutter',handler)
    server.addEventHandler('getsocket',handler)
    server.addEventHandler('testonline',handler)

    try:
        while True:
            logging.info("main: sleeping 3600 until next message (sleep forever)")
            time.sleep(3600)
    except:
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
