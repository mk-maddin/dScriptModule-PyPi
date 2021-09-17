#!/usr/bin/python
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: 
#   object capturing all incoming command triggers (protocol independend) and trowing events

from __future__ import annotations
import logging
_LOGGER = logging.getLogger(__name__)

from .dScriptObject import *
from threading import Thread
import asyncio
import _thread
import socket


class dScriptServer(dScriptObject):

    _EventHandlers = { 'heartbeat':[], 'getstatus':[], 'getrelay':[], 'getinput':[], 'getanalogue':[], 'getcounter':[], 'getconfig':[], 'getlight':[], 'getshutter':[], 'getsocket':[], 'getmotion':[], 'getbutton':[], 'testonline':[] }
    __server = None
    __thread = None
    __socketsize = 100
    __mode = None

    def __init__(self, TCP_IP='127.0.0.1', TCP_PORT=17123, PROTOCOL='binary'):
        _LOGGER.debug("dScriptServer - %s:%s: __init__", TCP_IP, TCP_PORT)
        self.IP = TCP_IP
        self.Port = TCP_PORT
        self.SetProtocol(PROTOCOL)
        self.State = False
        self.__server = None
        self.__thread = None

    def StartServer(self):
        _LOGGER.debug("dScriptServer - %s:%s: StartServer", self.IP, self.Port)
        if self.__mode == 'async':
            return self.async_StartServer()
        elif self.__mode == 'thread':
            return self.StartServer_async()
        if not self.__server is None or not self.__mode is None:            
            raise Exception("Server already started")
            return False
        try:
            self.__mode = 'init'
            self.__thread = Thread(target=self.__ServerThread)
            self.__thread.start()
            _LOGGER.debug("dScriptServer - %s:%s: StartServer - completed", self.IP, self.Port)
        except Exception as e: 
            _LOGGER.error("dScriptServer - %s:%s: StartServer failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)

    async def async_StartServer(self):
        _LOGGER.debug("dScriptServer - %s:%s: async_StartServer", self.IP, self.Port)
        if self.__mode == 'sync':
            return self.StartServer()
        elif self.__mode == 'thread':
            return self.StartServer_async()
        if not self.__server is None or not self.__mode is None:
            raise Exception("Server already running")
            return False
        try:
            loop = asyncio.get_event_loop()
            server_coro = await asyncio.start_server(self.__async_ClientConnected, self.IP, self.Port)
            if not loop.is_running():
                self.__server = loop.run_until_complete(server_coro)
            else:
                 self.__server = server_coro
            _LOGGER.info("dScriptServer - %s:%s: async_StartServer - serving on: %s:%s", self.IP, self.Port, self.IP, self.Port)
            self.State = self.__server.is_serving()
            self.__mode == 'thread'
            _LOGGER.debug("dScriptServer - %s:%s: async_StartServer - completed", self.IP, self.Port)
        except Exception as e: 
            _LOGGER.error("dScriptServer - %s:%s: async_StartServer failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)

    def StartServer_async(self):
        self.StartServer_async_thread()
            
    def StartServer_async_thread(self):
        _LOGGER.debug("dScriptServer - %s:%s: StartServer_async_thread", self.IP, self.Port)
        if self.__mode == 'sync':
            return self.StartServer()
        elif self.__mode == 'async':
            return self.async_StartServer()
        if not self.__server is None or not self.__mode is None:
            raise Exception("Server already running")
            return False
        try:
            self.__mode = 'init'
            self.__thread = Thread(target=self.__ServerThread_async)
            self.__thread.start()
            _LOGGER.debug("dScriptServer - %s:%s: StartServer_async_thread - completed", self.IP, self.Port)
        except Exception as e: 
            _LOGGER.error("dScriptServer - %s:%s: StartServer_async_thread failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)

    def StopServer(self):
        _LOGGER.debug("dScriptServer - %s:%s: StopServer_async", self.IP, self.Port)
        if self.__mode == 'async':
            return self.async_StopServer()
        elif self.__mode == 'thread':
            return self.StopServer_async()
        if self.__server == None:
            self.__server.shutdown(socket.SHUT_RDWR)
            raise Exception("Server already stopped")
        try:
            self.__server.close()
        except Exception as e:
            _LOGGER.error("dScriptServer: StopServer: Exception on server socket close: %s (%s.%s)", str(e), e.__class__.__module__, type(e).__name__)
            pass
        self.State = False
        self.__mode == None
        self.__server = None
        self.__thread = None

    async def async_StopServer(self):
        _LOGGER.debug("dScriptServer - %s:%s: async_StopServer", self.IP, self.Port)
        if self.__mode == 'sync':
            return self.StopServer()
        elif self.__mode == 'thread':
            return self.StopServer_async()
        if self.__server is None:
            raise Exception("Server already stopped")
        try:
            self.__server.close()
        except Exception as e: 
            _LOGGER.error("dScriptServer - %s:%s: async_StopServer failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)
            pass
        self.State = False
        self.__mode == None
        self.__server = None

    def StopServer_async(self):
        self.StopServer_async_thread()
        
    def StopServer_async_thread(self):
        _LOGGER.debug("dScriptServer - %s:%s: StopServer_async_thread", self.IP, self.Port)
        if self.__mode == 'sync':
            return self.StopServer()
        elif self.__mode == 'async':
            return self.async_StopServer()
        if self.__server is None:
            raise Exception("Server already stopped")
        try:
            self.__server.close()
        except Exception as e: 
            _LOGGER.error("dScriptServer - %s:%s: StopServer_async_thread failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)
            pass        
        self.State = False
        self.__mode == None
        self.__server = None
        self.__thread = None

    def __ServerThread(self):
        _LOGGER.debug("dScriptServer - %s:%s: ServerThread", self.IP, self.Port)
        try:
            self.__server = socket.socket()         # Create a socket object
            self.__server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            _LOGGER.error("dScriptServer - %s:%s: ServerThread failed on socket definition: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)
            return False

        try:
            self.__server.bind((self.IP, self.Port))
            self.__server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.__server.listen(5)     # Now wait for client connection.
            self.State = True
            _LOGGER.info("dScriptServer - %s:%s: ServerThread - serving on: (%s:%s)", self.IP, self.Port, self.IP, self.Port)
        except Exception as e:
            _LOGGER.error("dScriptServer - %s:%s: ServerThread failed on socket bind: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)
            return False
        
        try:
            while self.State:
               clientsocket, addr = self.__server.accept()     # Establish connection with client.
               _LOGGER.debug("dScriptServer - %s:%s: ServerThread: client connected: %s", self.IP, self.Port, addr)
               _thread.start_new_thread(self.__ClientConnected,(clientsocket,addr))
        except Exception as e:
            _LOGGER.error("dScriptServer - %s:%s: ServerThread failed on client connect: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)
            self.StopServer()
            pass
        _LOGGER.debug("dScriptServer - %s:%s: ServerThread - stopped serving on: (%s:%s)", self.IP, self.Port, self.IP, self.Port)

    def __ServerThread_async(self):
        _LOGGER.debug("dScriptServer - %s:%s: ServerThread_async", self.IP, self.Port)
        try:
            asyncio.run(self.__async_RunServerThread())
        except Exception as e: 
            _LOGGER.error("dScriptServer - %s:%s: ServerThread_async failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)
            
    async def __async_RunServerThread(self): 
        _LOGGER.debug("dScriptServer - %s:%s: async_RunServerThread", self.IP, self.Port)    
        try:
            self.__server = await asyncio.start_server(self.__async_ClientConnected, self.IP, self.Port)
            addr = self.__server.sockets[0].getsockname()
            _LOGGER.info("dScriptServer - %s:%s: async_RunServerThread - serving on: %s", self.IP, self.Port, addr)
        except Exception as e: 
            _LOGGER.error("dScriptServer - %s:%s: async_RunServerThread failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)
        try:
            await self.__server.start_serving()
            self.State = self.__server.is_serving()
            self.__mode == 'thread'
            _LOGGER.debug("dScriptServer - %s:%s: async_RunServerThread - started serving (%s) on: %s", self.IP, self.Port, self.__server.is_serving(), addr)
            while self.State:
                self.State = self.__server.is_serving()
                await asyncio.sleep(0)                
            _LOGGER.debug("dScriptServer - %s:%s: async_RunServerThread - stopped serving on: %s", self.IP, self.Port, addr)
        except Exception as e: 
            _LOGGER.error("dScriptServer - %s:%s: async_RunServerThread failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)
            self.StopServer_async()

    def __ClientConnected(self,clientsocket,addr):
        _LOGGER.debug("dScriptServer - %s:%s: ClientConnected: %s | %s", self.IP, self.Port, clientsocket, addr)
        try:
            data = clientsocket.recv(2) # received byte size is always 2 bytes from dScriptServerUpdate
            _LOGGER.debug("dScriptServer - %s:%s: ClientConnected: received data from: %s", self.IP, self.Port, addr)

            clientsocket.close()
            _LOGGER.debug("dScriptServer - %s:%s: ClientConnected: closed connection: %s", self.IP, self.Port, addr)
        except Exception as e:
            _LOGGER.error("dScriptServer - %s:%s: ClientConnected failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)
            #clientsocket.shutdown(socket.SHUT_RDWR)
            return False
        self.__InterpreteData(data,addr[0])

    async def __async_ClientConnected(self, reader, writer):
        _LOGGER.debug("dScriptServer - %s:%s: async_ClientConnected: %s | %s", self.IP, self.Port, reader, writer)  
        try:
            data = await reader.read(self.__socketsize) 
            #message = data.decode() 
            addr = writer.get_extra_info('peername') 
            _LOGGER.debug("dScriptServer - %s:%s: async_ClientConnected: received data from: %s", self.IP, self.Port, addr)

            writer.close()
            await asyncio.sleep(0)
            _LOGGER.debug("dScriptServer - %s:%s: async_ClientConnected: closed connection: %s", self.IP, self.Port, addr)
        except Exception as e: 
            _LOGGER.error("dScriptServer - %s:%s: async_ClientConnected failed: %s (%s.%s)", self.IP, self.Port, str(e), e.__class__.__module__, type(e).__name__)
            return False
        self.__InterpreteData(data,addr[0])
        
    def __InterpreteData(self,data,SenderIP):
        _LOGGER.debug("dScriptServer - %s:%s: InterpreteData: %s | %s", self.IP, self.Port, data, SenderIP)
        #TO-DO: identify protocol & select according action
        #if self._Protocol == self._Protocols[4]: #BinaryAES
        #    data=self._AESDecrypt(data)
        databytes=self._ToDataBytes(data)
        self.__InterpreteBinary(databytes,SenderIP)

    def __InterpreteBinary(self,databytes,SenderIP):
        _LOGGER.debug("dScriptServer - %s:%s: InterpreteBinary: %s | %s", self.IP, self.Port, databytes, SenderIP)
        if not self._IsInList(databytes[0],self._DecimalCommands.keys()):
            raise Exception("Unkown command: %s", databytes[0])
            return False
        cmd=self._DecimalCommands[databytes[0]].lower()
        
        if cmd == 'stopserver': 
            _LOGGER.info("dScriptServer - %s:%s: %s requested to stop server", self.IP, self.Port, SenderIP)
            self.StopServer()
        elif cmd == 'heartbeat' or cmd == 'getstatus' or cmd == 'getconfig' or cmd == 'testonline': #all of these do not need an identifier
            self._throwEvent(SenderIP, cmd)
        else:
            if len(databytes) == 3:
                if int(databytes[2]) < 0:
                    self._throwEvent(SenderIP, cmd, int(databytes[1]))
                elif cmd == 'getlight' or cmd == 'getsocket' or cmd == 'getmotion' or cmd == 'getrelay' or cmd == 'getinput':
                    self._throwEvent(SenderIP, cmd, int(databytes[1]), self._OnOffStates[databytes[2]])
                else:
                    self._throwEvent(SenderIP, cmd, int(databytes[1]), int(databytes[2]))
            else:
                self._throwEvent(SenderIP, cmd, int(databytes[1]))
        #return True
