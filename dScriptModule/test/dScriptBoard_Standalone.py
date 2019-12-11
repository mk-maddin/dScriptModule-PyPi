#!/usr/bin/env python
# version: 2018.10.05
# description: wrapper script to communicate with dsXXXX modules
#   this script uses the binary / binary AES encoding

##--imports required
import argparse
import logging
import socket
import struct
import sys

##--functions

##--classes

##--internal variables
moduleids = {'30':'dS3484', '31':'dS1242', '34':'dS2824', '35':'dS378'}
protids = {'1':'Modbus', '2':'ASCII', '3':'Binary', '4':'BinaryAES'}
onoff = {'0':'off', '1':'on'}
onoff_bit = 7
relay_max=32
io_max=8
degree_sign= u'\N{DEGREE SIGN}'

##--help text and script parameter processing
parser = argparse.ArgumentParser(description='Script interface to comunicate with dsXXXX modules using tcp/ip binary')
parser.add_argument('--hostname','-ip',required=True,help='Hostname or IP address of the dsXXXX module')
parser.add_argument('--port','-p',default=17123,help='Port the tcp server is listening to',type=int)
parser.add_argument('--buffer','-b',default=16,help='Buffer size for receive data in bytes',type=int)
parser.add_argument('--timeout','-t',default=2,help='Seconds until tcp request timeout',type=int)
parser.add_argument('--mode','-m',default='get',help='Set or get the status',choices=['set','get'])
parser.add_argument('--object','-o',default='status',help='Object type to get/set information on',choices=['status','relay','io','analogue','counter','config'])
parser.add_argument('--id','-i',default=0,help='ID of the object to get/set',type=int,choices=range(1,33))
parser.add_argument('--state','-s',help='State to set the object to',choices=['on','off'])

##--configure logging
#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)
logging.debug('parsing commandline arguments')
args=parser.parse_args()

##--build the binary command
if args.mode == 'get':
    logging.info('%s %s %s', args.mode, args.object, args.id)

    if args.object == 'status':
        msg='\x30'
    elif args.object == 'relay':
        msg='\x33'
    elif args.object == 'io':
        msg='\x34'
    elif args.object == 'analogue':
        msg='\x35'
    elif args.object == 'counter':
        msg='\x36'
    elif args.object =='config':
        msg='\x50'

    if not args.object == 'status' and not args.object == 'analogue' and not args.object == 'config': 
        logging.debug('adding object id')
        msg=msg + struct.pack("B",args.id)

elif args.mode == 'set':
    if args.state is None:
        logging.error('state parameter is required in set mode')
        sys.exit(22)
    logging.info('%s %s %s %s', args.mode, args.object, args.id, args.state)

    if args.object == 'relay':
        msg='\x31'
        if args.id > 24:
            logging.error('relays can be set only within a range of 1-24')
            sys.exit(22)
    elif args.object == 'io':
        msg='\x32'
    else:
        logging.error('%s object is not valid in set mode', args.object)
        sys.exit(22)

    logging.debug('adding object id byte')
    msg=msg + struct.pack("B",args.id)

    logging.debug('adding status byte')
    if args.state == 'on':
        state='\x01'
    else:
        state='\x00'
    msg=msg + state

    logging.debug('adding pulse bytes')
    if args.object == 'relay':
        msg = msg + '\x00\x00\x00\x00'

##--connect to the tcp server
logging.debug('connecting to: %s', args.hostname)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(args.timeout)
s.connect((args.hostname, args.port))

##--sending message
logging.debug('sending msg: %s', msg)
try:
    s.send(msg)
    data = s.recv(args.buffer)
except:
    logging.error('error while sending - closing connection')
    s.close()
    sys.exit(102)
s.close()

##--convert the result for further processing
databytes = [str(ord(x)) for x in data]
logging.debug('recieved databytes: %s', databytes)
databits = ''.join(format(ord(byte), '08b') for byte in data)
logging.debug('recieved databits: %s', databits)

if args.object == 'status':
    logging.info('module: %s', moduleids[databytes[0]])
    logging.info('system firmware: %s.%s', databytes[1],databytes[2])
    logging.info('program firmware: %s.%s', databytes[3],databytes[4])
    logging.info('power supply: %sv', float(databytes[5])/10.00)
    logging.info ('internal degree: %s%sC', int(databits[(6*8):(8*8)],2)/10.00, degree_sign)
if args.object == 'config':
    logging.info('module: %s', moduleids[databytes[0]])
    logging.info ('tcpport: %s', int(databits[(1*8):(8*8)],2)/10.00)
    logging.info('protocol: %s', protids[databytes[3]]) 
    logging.info('pysical relays: %s', databytes[4])
    logging.info('lights: %s', databytes[5])
    logging.info('shutters: %s', databytes[6])
    logging.info('sockets: %s', databytes[7])
elif args.mode == 'set':
    if not databits == '00000000':
        logging.error('error setting state: 0x%s', databits)
        sys.exit(11)
    logging.info('success')
    sys.exit(0)
elif args.mode == 'get':
    if args.object == 'relay' or args.object == 'io':
        logging.info ('requested %s %s state is: %s', args.object, args.id, onoff[databits[onoff_bit]])
        
        if args.object == 'relay':
            ids=range(relay_max,0,-1)
        elif args.object == 'io':
            ids=range(io_max,0,-1)

        a=onoff_bit  
        for i in ids:
            a += 1
            logging.info('%s %s state is: %s', args.object, i, onoff[databits[a]])    
    #TO-DO: analogue & counter

