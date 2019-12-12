#!/usr/bin/python
# version: 2019.08.09
# author: Martin Kraemer, mk.maddin@gmail.com
# description: 
#   object capturing all incoming command triggers (protocol independend) and trowing events

from .dScriptObject import *
from .dScriptEvent import *
import _thread
import socket

class dScriptServer(dScriptObject):

    __socket = None
    _evt_HeartBeat = Event(SenderIP)
    _evt_GetStatus = Event(SenderIP)
    _evt_GetConfig = Event(SenderIP)
    _evt_GetLight = Event(SenderIP,identifier)
    _evt_GetShutter = Event(SenderIP,identifier)
    _evt_GetSocket = Event(SenderIP,identifier)

    def __init__(self, TCP_IP='0.0.0.0', TCP_PORT=17123, PROTOCOL='binary'):
        logging.debug("dScriptServer: __init__")
        self.IP = TCP_IP
        self.Port = TCP_PORT
        self.SetProtocol(PROTOCOL)
        self.__socket = None

    def StartServer(self):
        logging.debug("dScriptServer: StartServer")
        if not self.__socket == None:
            return False
        _thread.start_new_thread(self.__ServerThread,())

    def StopServer(self):
        logging.debug("dScriptServer: StopServer")
        if self.__socket == None:
            return False
        self.__socket.close()
        self.__socket = None

    def __ServerThread(self):
        logging.debug("dScriptServer: __ServerThread")
        self.__socket = socket.socket()         # Create a socket object
        self.__socket.bind((self.IP, self.Port))
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.listen(5)                 # Now wait for client connection.
        logging.info("dScriptServer: Started - waiting for clients...")
        try:
            while True:
               c, addr = self.__socket.accept()     # Establish connection with client.
               logging.debug("dScriptServer: Client connected: %s", addr)
               _thread.start_new_thread(self.__ClientConnected,(c,addr))
        except:
            pass
        logging.info("dScriptServer: Stopped - closing server")
        self.__socket.close()
        self.__socket = None

    def __ClientConnected(self,clientsocket,addr):
        logging.debug("dScriptServer: __ClientConnected")
        data = clientsocket.recv(2) # received byte size is always 2 bytes from dScriptServerUpdate
        logging.debug("dScriptServer: Close connection: %s", addr)
        clientsocket.close()
        self.__InterpreteData(data,addr[0])

    def __InterpreteData(data,SenderIP):
        logging.debug("dScriptServer: __InterpreteData")
        #TO-DO: identify protocol & select according action
        if self._Protocol == self._Protocols[4]: #BinaryAES
            data=self._AESDecrypt(data)
        databytes=self.__ToDataBytes(data)
        self.__InterpreteBinary(databytes,SenderIP)

    def __InterpreteBinary(databytes,SenderIP):
        if databytes[0] == '0':
            logging.debug("dScriptServer: HeartBeat: %s", SenderIP)
            self._evt_HeartBeat(SenderIP)
        elif databytes[0] == '48': # '\x30':
            logging.debug("dScriptServer: GetStatus: %s", SenderIP)
            self._evt_GetStatus(SenderIP)
        #elif databytes[0] == '51': # '\x33':
        #    logging.debug("dScriptServer: GetRelay")   # TO-DO: implement
        #elif databytes[0] == '52': # '\x34':
        #    logging.debug("dScriptServer: GetInput")   # TO-DO: implement
        #elif databytes[0] == '53': # '\x35':
        #    logging.debug("dScriptServer: GetAnalogue")# TO-DO: implement
        #elif databytes[0] == '54': # '\x36':
        #    logging.debug("dScriptServer: GetCounter") # TO-DO: implement
        elif databytes[0] == '80': # '\x50':
            logging.debug("dScriptServer: GetConfig: %s", SenderIP)
            self._evt_GetConfig(SenderIP)
        elif databytes[0] == '81': # '\x51':
            logging.debug("dScriptServer: GetLight: %s", SenderIP)
            self._evt_GetLight(SenderIP,int(databytes[1]))
        elif databytes[0] == '82': # '\x52':
            logging.debug("dScriptServer: GetShutter: %s", SenderIP)
            self._evt_GetShutter(SenderIP,int(databytes[1]))
        elif databytes[0] == '83': # '\x53':
            logging.debug("dScriptServer: GetSocket: %s", SenderIP)
            self._evt_GetSocket(SenderIP,int(databytes[1]))
        else:
            raise Exception("Unkown command: %s", databytes[0])
            return False

