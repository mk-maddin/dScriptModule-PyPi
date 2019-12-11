#!/usr/bin/python
# version: 2019.08.09
# author: Martin Kraemer, mk.maddin@gmail.com
# descrIPtion: 
#   python library containing all types of engines
# usage examples:

import logging
import socket
import struct
import thread

class dScriptBoard(object):

    #attributes of object
    _HostName = ''
    #IP = '127.0.0.1'
    #Port = 17123
    CMDProtocol = 'binary'
    __AESKey = ''
    __Nonce = ''
    __ModuleIDs = {'30':'dS3484', '31':'dS1242', '34':'dS2824', '35':'dS378'}
    __Protocols = {'1':'Modbus', '2':'ASCII', '3':'Binary', '4':'BinaryAES'}
    __OnOffIDs = {'0':'off', '1':'on'}
    __MoveIDs = {'0':'stopped', '1':'opening', '2':'closing'}

    '''Initialize the dScriptBoard element with at least its IP and port to be able to connect later'''
    def __init__(self, TCP_IP, TCP_PORT=17123):
        logging.debug("dScriptBoard: __init__")
        self.IP = TCP_IP
        self.Port = TCP_PORT
        self.GetHostName()

    #def detect_CMDProtocol(self):
    #    logging.debug("dScriptBoard: detect_CMDProtocol")

    '''Wrapper function to send a message to the board via the configured protocol'''
    def __Send(self,msg,buff):
        logging.debug("dScriptBoard: __Send: %s | %s",msg,buff)
        if self.CMDProtocol == 'binaryaes':
            return self.__SendBinaryAES(msg,buff)
        else:
            return self.__SendBinary(msg,buff)

    '''Send and recieve the result of a message to the board via binary protocol'''
    def __SendBinary(self,msg,buff):
        logging.debug("dScriptBoard: __SendBinary: %s | %s",msg,buff)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #s.settimeout(2)
        s.connect((self.IP, self.Port))
        try:
            s.send(msg)
            data = s.recv(buff)
        except:
            logging.error("dScriptBoard: could not send - closing connection")
            self.__socket.close()
            return False
        s.close()
        return data

    '''Send and receive the result of a message to the board via AES encrypted binary protocol'''
    def __SendBinaryAES(self,msg,buff):
        logging.debug("dScriptBoard: __SendBinaryAES: %s | %s",msg,buff)
        #get & set the __Nonce on reply
        #decrypt message to binary only reply
        return False
   
    '''Translate received set of data into byte array'''
    def __ToDataBytes(self,data):
        logging.debug("dScriptBoard: __ToDataBytes: %s",data)
        databytes = [str(ord(x)) for x in data]
        logging.debug("dScriptBoard: received databytes: %s", databytes)
        return databytes

    '''Translate received set of data into bit array'''
    def __ToDataBits(self,data):
        logging.debug("dScriptBoard: __ToDataBits: %s",data)
        databits = ''.join(format(ord(byte), '08b') for byte in data)
        logging.debug("dScriptBoard: received databits: %s", databits)
        return databits
    
    def __MatchState(self,state):
        logging.debug("dScriptBoard: __MatchState: %s",state)
        state=state.lower()
        if state == 'on': 
            return 1
        elif state == 'off': 
            return 0
        else: #trigger
            return 2

    '''Set the protocol used to communicate with this board'''
    def SetProtocol(self, PROTOCOL='binary'): # binary is the default CMDProtocol
        logging.debug("dScriptBoard: SetProtocol: %s",PROTOCOL)
        PROTOCOL=PROTOCOL.lower()
        if PROTOCOL == 'binaryaes' and not self.__AESKey:
            logging.error("dScriptBoard: AES key is required for BinaryAES CMDProtocol")
        else:
            self.CMDProtocol = PROTOCOL

    '''Set the AES key used for communication via the AESBinary protocol'''
    def SetAESKey(self, KEY):
        logging.debug("dScriptBoard: SetAESKey: XXXX")
        if not len(KEY) == 32:
            logging.error("dScriptBoard: AES key needs to have a exact length of 32 characters")
            return
        self.__AESKey = KEY
        if not self.__AESKey and self.CMDProtocol == 4: #if aes key is empty and current CMDProtocol is BinaryAES switch to binary
            logging.info("dScriptBoard: switching to CMDProtocol: Binary")
            self.SetProtocol('binary')
        elif self.__AESKey and self.CMDProtocol == 3:   #if aes key is not empty and current CMDProtocol is Binary switch to BinaryAES
            logging.info("dScriptBoard: switching to CMDProtocol: BinaryAES")
            self.SetProtocol('binaryaes')

    '''Print the status of this dScriptModule object'''
    def PrintInfo(self):
        logging.debug("dScriptBoard: PrintInfo")
        for attr in dir(self):
            if hasattr( self, attr ):
                logging.info("dScriptBoard: %s: %s = %s", self._HostName, attr, getattr(self, attr))

    '''Find the hostname of this device - using dns resolution - and write it as an attribute'''
    def GetHostName(self):
        logging.debug("dScriptBoard: GetHostName")
        self._HostName = socket.gethostbyaddr(self.IP)[0]
        if not self._HostName:
            self._HostName = self.IP

    '''Execute the GS, GetStatus command on the board and write its results as attributes'''
    def GetStatus(self):
        logging.debug("dScriptBoard: GetStatus")
        data=self.__Send('\x30',8) # GetStatus = 0x30 and returns 8 bytes
        databytes=self.__ToDataBytes(data)
        databits=self.__ToDataBits(data)

        logging.info("dScriptBoard: %s: Update board status information", self._HostName) 
        self._ModuleID=self.__ModuleIDs[databytes[0]]
        self._SystemFirmwareMajor=databytes[1]
        self._SystemFirmwareMinor=databytes[2]
        self._ApplicationFirmwareMajor=databytes[3]
        self._ApplicationFirmwareMinor=databytes[4]
        self._Volts=float(databytes[5])/10.00
        self._Temperature=int(databits[(6*8):(8*8)],2)

    '''Execute the GC, GetConfig command on the board and write its results as attributes'''
    def GetConfig(self):
        logging.debug("dScriptBoard: GetConfig")
        data=self.__Send('\x50',8) # GetConfig = 0x50 and returns 8 bytes
        databytes=self.__ToDataBytes(data)
        databits=self.__ToDataBits(data)
       
        logging.info("dScriptBoard: %s: Update board config information", self._HostName)
        self._ModuleID=self.__ModuleIDs[databytes[0]]
        self._TCPPort=int(databits[(1*8):(8*8)],2)          # written as "nice to have"
        self._TCPProtocol=self.__Protocols[databytes[3]]    # written as "nice to have" 
        self._PhysicalRelays=databytes[4]
        self._ConnectedLights=databytes[5]
        self._ConnectedShutters=databytes[6]
        self._ConnectedSockets=databytes[7]

    '''Execute the GL, GetLight command and print the result into log'''
    def GetLight(self,identifier):
        logging.debug("dScriptBoard: GetLight: %s",identifier)
        if identifier <= 0 or identifier  > self._ConnectedLights:
            logging.error("dScriptBoard: Maximum connected light is: %s", self._ConnectedLights)
            return False
        msg='\x51' # GetLight = 0x51 and returns 1 byte
        msg=msg + struct.pack("B",identifier)
        data=self.__Send(msg,1)
        databytes=self.__ToDataBytes(data)
        logging.info("dScriptBoard: %s: Light %s is %s", self._HostName, identifier, self.__OnOffIDs[databytes[0]])

    '''Execute the GH, GetShutter command and print the result into log'''
    def GetShutter(self,identifier):
        logging.debug("dScriptBoard: GetShutter: %s",identifier)
        if identifier <= 0 or identifier  > self._ConnectedShutters:
            logging.error("dScriptBoard: Maximum connected shutter is: %s", self._ConnectedShutters)
            return False
        msg='\x52' # GetShutter = 0x52 and returns 2 bytes
        msg=msg + struct.pack("B",identifier)
        data=self.__Send(msg,2)
        databytes=self.__ToDataBytes(data)
        logging.info("dScriptBoard: %s: Shutter %s is %s at level %s%%", self._HostName, identifier, self.__MoveIDs[databytes[1]], databytes[0])

    '''Execute the GC, GetSocket command and print the result into log'''
    def GetSocket(self,identifier):
        logging.debug("dScriptBoard: GetSocket: %s",identifier)
        if identifier <= 0 or identifier  > self._ConnectedSockets:
            logging.error("dScriptBoard: Maximum connected socket is: %s", self._ConnectedSockets)
            return False
        msg='\x53' # GetSocket = 0x53 and returns 1 byte
        msg=msg + struct.pack("B",identifier)
        data=self.__Send(msg,1)
        databytes=self.__ToDataBytes(data)
        logging.info("dScriptBoard: %s: Socket %s is %s", self._HostName, identifier, self.__OnOffIDs[databytes[0]])

    '''Execute the SL, SetLight command to define a light status'''
    def SetLight(self,identifier,state):
        logging.debug("dScriptBoard: SetLight: %s | %s",identifier,state)
        if identifier <= 0 or identifier  > self._ConnectedLights:
            logging.error("dScriptBoard: Maximum connected light is: %s", self._ConnectedLights)
            return False
        istate=self.__MatchState(state)
        msg='\x40' + struct.pack("B",identifier) + struct.pack("B",istate) # SetLight = 0x40 and returns 1 byte
        data=self.__Send(msg,1)
        databytes=self.__ToDataBytes(data)
        if databytes[0] != 0:
            logging.error("dScriptBoard: Could not set light %s to %s - return %s",identifier,state,databytes[0])
            return False

    '''Execute the SH, SetShutter command to define a shutter status'''
    def SetShutter(self,identifier,state):
        logging.debug("dScriptBoard: SetShutter: %s | %s",identifier,state)
        if identifier <= 0 or identifier  > self._ConnectedShutter:
            logging.error("dScriptBoard: Maximum connected shutter is: %s", self._ConnectedShutter)
            return False
        if state > 100: #state can be max 100 = Fully Open
            state = 100
        elif state < 0: #state can be min 0 = Fully Closed
            state = 0
        msg='\x41' + struct.pack("B",identifier) + struct.pack("B",state) # SetShutter = 0x41 and returns 1 byte
        data=self.__Send(msg,1)
        databytes=self.__ToDataBytes(data)
        if databytes[0] != 0:
            logging.error("dScriptBoard: Could not set shutter %s to %s - return %s",identifier,state,databytes[0])
            return False

    '''Execute the SC, SetSocket command to define a socket status'''
    def SetSocket(self,identifier,state):
        logging.debug("dScriptBoard: SetSocket: %s | %s",identifier,state)
        if identifier <= 0 or identifier  > self._ConnectedSockets:
            logging.error("dScriptBoard: Maximum connected socket is: %s", self._ConnectedSockets)
            return False
        istate=self.__MatchState(state)
        msg='\x42' + struct.pack("B",identifier) + struct.pack("B",istate) # SetSocket = 0x42 and returns 1 byte
        data=self.__Send(msg,1)
        databytes=self.__ToDataBytes(data)
        if databytes[0] != 0:
            logging.error("dScriptBoard: Could not set socket %s to %s - return %s",identifier,state,databytes[0])
            return False

class dScriptServer(object):
    
    #attributes of object
    #IP = '0.0.0.0'
    #Port = 17123
    __socket = ''
    #CMDProtocol = 'binary' 
    __AESKey = ''
    dScriptBoards = []

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
        thread.start_new_thread(self.__ServerThread,())

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
               thread.start_new_thread(self.__ClientConnected,(c,addr))
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

        ##--convert the result for further processing into bytes
        databytes = [str(ord(x)) for x in data]
        logging.debug("dScriptServer: Recieved databytes: %s", databytes)
        self.__InterpreteData(databytes,addr) 
    
    def __InterpreteData(self,databytes,addr):
        logging.debug("dScriptServer: __InterpreteData")
        board=self.__GetBoard(addr[0]) # search if the board exists based on IP
        if databytes[0] == '0': # '\x00'; "master I am here" trigger
            if not board:       # add new board if it not already exists
                logging.info("dScriptServer: New dScript board: %s", addr)
                self.__AddBoard(addr)
            else:               # ensure board configuration is still valid after new boot
                logging.info("dScriptServer: Existing board heartbeat: %s", addr)
                board.GetStatus()
                board.GetConfig()
                #board.PrintInfo()
            return

        if not board: #all following commands require an existing board
            logging.error("dScriptServer: Source is not an existing board: %s", addr[0])
            logging.debug("dScriptServer: Sent initial command of '\x00' to register board")
            return
        elif databytes[0] == '48': # '\x30':
            logging.debug("dScriptServer: GetStatus")
            board.GetStatus()
        elif databytes[0] == '51': # '\x33':
            logging.debug("dScriptServer: GetRelay")   # TO-DO: create and call function within dScriptBoard class
        elif databytes[0] == '52': # '\x34':
            logging.debug("dScriptServer: GetInput")   # TO-DO: create and call function within dScriptBoard class
        elif databytes[0] == '53': # '\x35':
            logging.debug("dScriptServer: GetAnalogue")# TO-DO: create and call function within dScriptBoard class
        elif databytes[0] == '54': # '\x36':
            logging.debug("dScriptServer: GetCounter") # TO-DO: create and call function within dScriptBoard class
        elif databytes[0] == '80': # '\x50':
            logging.debug("dScriptServer: GetConfig")
            board.GetConfig()
        elif databytes[0] == '81': # '\x51':
            logging.debug("dScriptServer: GetLight")
            board.GetLight(int(databytes[1]))
        elif databytes[0] == '82': # '\x52':
            logging.debug("dScriptServer: GetShutter")
            board.GetShutter(int(databytes[1]))
        elif databytes[0] == '83': # '\x53':
            logging.debug("dScriptServer: GetSocket")
            board.GetSocket(int(databytes[1]))
        else:
            logging.info("dScriptServer: Unknown command byte!")

    def __AddBoard(self,addr):
        logging.debug("dScriptServer: __AddBoard")
        newboard = dScriptBoard(addr[0], self.Port) # the clients server Port must always be equal to server Port
        if self.__AESKey:
            newboard.SetAESKey(self.__AESKey)   # if server has an __AESKey set, take it over for the board
        newboard.SetProtocol(self.CMDProtocol)  # use current server CMDProtocol as default CMDProtocol
        newboard.GetStatus()                    # update status information of the board
        newboard.GetConfig()                    # update configuration information of the board
        #newboard.PrintInfo()                   # print all information about the new board
        self.dScriptBoards.append(newboard)
    
    def __GetBoard(self,addr):
        logging.debug("dScriptServer: __GetBoard")
        for x in self.dScriptBoards:
                if x.IP == addr:
                    return x
        return False

    def SetProtocol(self, PROTOCOL='binary'): # binary is the default CMDProtocol
        logging.debug("dScriptServer: SetProtocol")
        PROTOCOL=PROTOCOL.lower()
        if PROTOCOL == 'binaryaes' and not self.__AESKey:
            logging.error("dScriptServer: error: AES key is required for BinaryAES CMDProtocol")
        else:
            self.CMDProtocol = PROTOCOL

    def SetAESKey(self, KEY):
        logging.debug("dScriptServer: SetAESKey")
        if not len(KEY) == 32:
            logging.info("dScriptServer: error: AES key needs to have a exact length of 32 characters")
            return
        self.__AESKey = KEY
        if not self.__AESKey and self.CMDProtocol == 4: #if aes key is empty and current CMDProtocol is BinaryAES switch to binary
            logging.info("dScriptServer: switching to CMDProtocol: Binary")
            self.SetProtocol('binary')
        elif self.__AESKey and self.CMDProtocol == 3:   #if aes key is not empty and current CMDProtocol is Binary switch to BinaryAES
            logging.info("dScriptServer: switching to CMDProtocol: BinaryAES")
            self.SetProtocol('binaryaes')

