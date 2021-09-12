#!/usr/bin/env python
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: script to test the dScriptServer and corresponding classes

import sys
import logging as _LOGGER
import time

def handler(sender, earg):
    _LOGGER.info("handler: executed")

    attrlist=[ 'sender', 'topic', 'identifier', 'value' ]
    for attr in attrlist:
        if hasattr(sender, attr ):
            _LOGGER.debug("handler: SENDER: %s = %s", attr, getattr(sender, attr))

#    #_LOGGER.debug("handler: showing sender attributes")
#    for attr in dir(sender):
#        if hasattr(sender, attr ):
#            _LOGGER.debug("handler: SENDER: %s = %s", attr, getattr(sender, attr))

#    #_LOGGER.debug("handler: showing earg attributes")
#    for attr in dir(earg):
#        if hasattr(earg, attr ):
#            _LOGGER.debug("handler: EARG: %s = %s", attr, getattr(earg, attr))


def main():
    _LOGGER.info("main: starting program...")
    from dScriptModule import dScriptServer

    _LOGGER.debug("main: create dScriptServer object")
    server = dScriptServer()

    _LOGGER.debug("main: starting server")
    server.StartServer()

    _LOGGER.debug("main: register handler")
    server.addEventHandler('heartbeat',handler)
    server.addEventHandler('getstatus',handler)
    server.addEventHandler('getconfig',handler)
    server.addEventHandler('getlight',handler)
    server.addEventHandler('getshutter',handler)
    server.addEventHandler('getsocket',handler)
    server.addEventHandler('getmotion',handler)
    server.addEventHandler('testonline',handler)

    try:
        while True:
            _LOGGER.info("main: sleeping 3600 until next message (sleep forever)")
            time.sleep(3600)
    except:
        pass
    _LOGGER.debug("main: keyboard interrupted")

    _LOGGER.debug("main: stopping server")
    server.StopServer()

    _LOGGER.debug("main: exit now - BYE BYE")
    sys.exit()

#_LOGGER.basicConfig(format='%(levelname)s:%(message)s', level=_LOGGER.DEBUG)
_LOGGER.basicConfig(level=_LOGGER.DEBUG)
#_LOGGER.basicConfig(level=_LOGGER.INFO)
main()
