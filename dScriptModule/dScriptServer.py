#!/usr/bin/python
# version: 2019.08.09
# author: Martin Kraemer, mk.maddin@gmail.com
# description: 
#   object capturing all incoming command triggers (protocol independend) and trowing events

from .dScriptObject import *
import _thread
import socket

class dScriptServer(dScriptObject):

    __socket = None

    _EventHandlers = { 'heartbeat':[], 'getstatus':[], 'getrelay':[], 'getinput':[], 'getanalogue':[], 'getcounter':[], 'getconfig':[], 'getlight':[], 'getshutter':[], 'getsocket':[] }

    def __init__(self, TCP_IP='0.0.0.0', TCP_PORT=17123, PROTOCOL='binary'):
        #logging.debug("dScriptServer: __init__")
        self.IP = TCP_IP
        self.Port = TCP_PORT
        self.SetProtocol(PROTOCOL)
        self.__socket = None

    def StartServer(self):
        #logging.debug("dScriptServer: StartServer")
        if not self.__socket == None:
            raise Exception("Server already started")
            return False
        _thread.start_new_thread(self.__ServerThread,())

    def StopServer(self):
        #logging.debug("dScriptServer: StopServer")
        if self.__socket == None:
            raise Exception("Server already stopped")
            return False
        self.__socket.close()
        self.__socket = None

    def __ServerThread(self):
        #logging.debug("dScriptServer: __ServerThread")
        self.__socket = socket.socket()         # Create a socket object
        self.__socket.bind((self.IP, self.Port))
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.listen(5)                 # Now wait for client connection.
        logging.info("dScriptServer: Started - waiting for clients...")
        try:
            while True:
               c, addr = self.__socket.accept()     # Establish connection with client.
               #logging.debug("dScriptServer: Client connected: %s", addr)
               _thread.start_new_thread(self.__ClientConnected,(c,addr))
        except:
            pass
        logging.info("dScriptServer: Stopped - closing server")
        self.__socket.close()
        self.__socket = None

    def __ClientConnected(self,clientsocket,addr):
        #logging.debug("dScriptServer: __ClientConnected")
        data = clientsocket.recv(2) # received byte size is always 2 bytes from dScriptServerUpdate
        #logging.debug("dScriptServer: Close connection: %s", addr)
        clientsocket.close()
        self.__InterpreteData(data,addr[0])

    def __InterpreteData(self,data,SenderIP):
        #logging.debug("dScriptServer: __InterpreteData")
        #TO-DO: identify protocol & select according action
        if self._Protocol == self._Protocols[4]: #BinaryAES
            data=self._AESDecrypt(data)
        databytes=self._ToDataBytes(data)
        self.__InterpreteBinary(databytes,SenderIP)

    def __InterpreteBinary(self,databytes,SenderIP):
        if not self._IsInList(databytes[0],self._DecimalCommands.keys()):
            raise Exception("Unkown command: %s", databytes[0])
            return False
        cmd=self._DecimalCommands[databytes[0]].lower()
        
        if cmd == 'heartbeat' or cmd == 'getstatus' or cmd == 'getconfig': #all of these do not need an identifier
            self._throwEvent(SenderIP, cmd)
        else:
            self._throwEvent(SenderIP, cmd, int(databytes[1]))
        return True

