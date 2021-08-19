#!/usr/bin/python
# version: 2021.06.09
# author: Martin Kraemer, mk.maddin@gmail.com
# description: 
#   object capturing all incoming command triggers (protocol independend) and trowing events

import logging
_LOGGER = logging.getLogger(__name__)

from .dScriptObject import *
import _thread
import socket
import time

class dScriptServer(dScriptObject):

    __socket = None

    _EventHandlers = { 'heartbeat':[], 'getstatus':[], 'getrelay':[], 'getinput':[], 'getanalogue':[], 'getcounter':[], 'getconfig':[], 'getlight':[], 'getshutter':[], 'getsocket':[], 'getmotion':[], 'getbutton':[], 'testonline':[] }

    def __init__(self, TCP_IP='0.0.0.0', TCP_PORT=17123, PROTOCOL='binary'):
        _LOGGER.debug("dScriptServer: __init__")
        self.IP = TCP_IP
        self.Port = TCP_PORT
        self.SetProtocol(PROTOCOL)
        self.State = False
        self.__socket = None

    def StartServer(self):
        _LOGGER.debug("dScriptServer: StartServer")
        if not self.__socket == None:
            raise Exception("Server already started")
            return False
        _thread.start_new_thread(self.__ServerThread,())

    def StopServer(self):
        _LOGGER.debug("dScriptServer: StopServer")
        if self.__socket == None:
            self.__socket.shutdown(socket.SHUT_RDWR)
            raise Exception("Server already stopped")
            return False
        try:
            self.__socket.close()
        except Exception as e: 
            _LOGGER.debug("dScriptServer: StopServer: Exception on server socket close: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)
            pass
        self.__socket = None
        self.State = False

    def __ServerThread(self):
        _LOGGER.debug("dScriptServer: __ServerThread")
        stopped=True
        failedc=0
        while stopped and failedc < 5:
            try:
                self.__socket = socket.socket()         # Create a socket object
                self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                stopped=False
            except Exception as e: 
                faliedc+=1
                _LOGGER.info("dScriptServer: Warning startup failed %s times...", failedc)
                _LOGGER.debug("dScriptServer: _ServerThread: Exception on server socket creation: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)
                time.sleep(5)
        if failedc >= 5:
            return False
        try:
            self.__socket.bind((self.IP, self.Port))
            self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #self.__socket.settimeout(self.ConnectionTimeout)
            self.__socket.listen(5)                 # Now wait for client connection.
            self.State = True
        except Exception as e: 
            _LOGGER.debug("dScriptServer: _ServerThread: Exception on server socket listen: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)
        _LOGGER.info("dScriptServer: Started - waiting for clients...")
        try:
            while True:
               clientsocket, addr = self.__socket.accept()     # Establish connection with client.
               _LOGGER.debug("dScriptServer: Client connected: %s", addr)
               _thread.start_new_thread(self.__ClientConnected,(clientsocket,addr))
        except Exception as e: 
            _LOGGER.debug("dScriptServer:_ServerThread: Exception on client connected thread: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)
            pass
        _LOGGER.info("dScriptServer: Stopped - closing server")
        try:
            for attr in dir(self.__socket):
                if hasattr(self.__socket, attr ):
                    _LOGGER.debug("SOCKET: %s = %s", attr, getattr(self.__socket, attr))

            self.__socket.close()
        except Exception as e: 
            _LOGGER.debug("dScriptServer: _ServerThread: Exception on server socket close: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)
            self.__socket.shutdown(socket.SHUT_RDWR) 
            pass
        self.__socket = None
        self.State = False

    def __ClientConnected(self,clientsocket,addr):
        _LOGGER.debug("dScriptServer: __ClientConnected")
        data = clientsocket.recv(2) # received byte size is always 2 bytes from dScriptServerUpdate
        try:
            clientsocket.close()
            _LOGGER.debug("dScriptServer: __ClientConnected: Closed connection: %s", addr)
        except Exception as e: 
            _LOGGER.debug("dScriptServer: __ClientConnected: Exception on client socket close: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)
            clientsocket.shutdown(socket.SHUT_RDWR)
            pass
        self.__InterpreteData(data,addr[0])

    def __InterpreteData(self,data,SenderIP):
        _LOGGER.debug("dScriptServer: __InterpreteData")
        #TO-DO: identify protocol & select according action
        #if self._Protocol == self._Protocols[4]: #BinaryAES
        #    data=self._AESDecrypt(data)
        databytes=self._ToDataBytes(data)
        self.__InterpreteBinary(databytes,SenderIP)

    def __InterpreteBinary(self,databytes,SenderIP):
        if not self._IsInList(databytes[0],self._DecimalCommands.keys()):
            raise Exception("Unkown command: %s", databytes[0])
            return False
        cmd=self._DecimalCommands[databytes[0]].lower()
        
        if cmd == 'stopserver': 
            _LOGGER.info("dScriptServer: %s requested to stop server", SenderIP)
            self.StopServer()
        elif cmd == 'heartbeat' or cmd == 'getstatus' or cmd == 'getconfig' or cmd == 'testonline': #all of these do not need an identifier
            self._throwEvent(SenderIP, cmd)
        else:
            self._throwEvent(SenderIP, cmd, int(databytes[1]))
        return True

