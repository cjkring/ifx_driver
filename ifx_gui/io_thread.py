# -*- coding: utf-8 -*-
"""
Created on Sun Dec  6 16:07:56 2020

@author: cjkri
"""

import logging
import time
import socket
from struct import unpack
import numpy as np
import rd_store
import serial
import serial.tools.list_ports


samples_per_packet = 256
#seek in data for DEADBEEF, then get 12 bytes of data after that.  Data can 
#spread across multiple data packets.
def marshall(readings,data):
    

    
    packet_len = samples_per_packet * 4 + 4 # has to match driver, include seqno and count
    i = 0
    
    length = len(data)
    
    if marshall.looking == 1:
        # have found a DEADBEEF now looking for payload
        if(len(marshall.last) + len(data) >= packet_len):  
            # sufficient data - concat and parse
            i = packet_len - len(marshall.last)
            parse_data(readings,marshall.last + data[:i],1)
            marshall.last = b''
        else:
            #insuffient data to parse,  add to last and keep going
            #print("appending to marshall.last")
            marshall.last = marshall.last + data 
            return
    
    # seek for DEADBEEF
    marshall.looking = 0
    while i  < length - 3:
          
        #print("data",list(data[i:]), "i=",i,"length=",length)
        
        if(data[i:i+4] == b'\xde\xad\xbe\xef'):
            marshall.looking = 1
            i = i + 4
            #print('i=',i,',len=',length)
            if i == length:
                #end of buffer
                #print("resetting marshall.last")
                marshall.last = b''
                return
            elif i > length - packet_len:
                #some data 
                #print("setting marshall.last")
                marshall.last =  data[i:]
                return
            else:
                parse_data(readings,data[i:i+packet_len],2)
                i = i + packet_len
                marshall.looking = 0
            
        else:
            i = i + 1

def parse_data(readings,packet, loc):       

    #print("parsing: ",loc,',', list(packet))

    reading_array = np.empty(samples_per_packet, dtype=complex)

    try:
        (seqno, count) = unpack( '!HH', packet[0:4] )
        parse_data.prev_seqno = seqno
        #reading_array = np.empty(count, dtype=complex)
        for j in range( count ):
            idx = 4 + 4 * j
            (I,Q) = unpack( '!HH', packet[idx:idx+4] )
            # the device returns raw ADC readings that hover around 2000,2000
            # this generates a baseline that moves the average reading to about 0,0
            if parse_data.avg_count < 1000: 
                parse_data.sum_i += I
                parse_data.sum_q += Q
                parse_data.avg_count += 1
                parse_data.avg_i = int(parse_data.sum_i / parse_data.avg_count)
                parse_data.avg_q = int(parse_data.sum_q / parse_data.avg_count)
            I = int(I - parse_data.avg_i)
            Q = int(Q - parse_data.avg_q)

            reading_array[j] = complex(I,Q)
            #print(reading)
        #print(loc,',',seqno,',',len(reading_array),',',reading_array[0],',',reading_array[-1])
        readings.put(rd_store.Reading(seqno,count,reading_array))
    except Exception as e:
        print(f'parsing exception: dropping packet after {seqno}:{e}')
        return;

parse_data.avg_count = 0
parse_data.sum_i = 0
parse_data.sum_q = 0
parse_data.avg_i = 0
parse_data.avg_q = 0
        
           
marshall.looking = 0
marshall.last = b''
parse_data.prev_seqno = 0

# this is the interface to the Sense2Go module via a USB CDC serial port

def io_thread_impl(queue):
    logging.warning("IO Thread started")

    
    port = None
    for p in serial.tools.list_ports.comports():
        if p.vid == 4966 and p.pid == 261:
            port = p
            print(f'Found: {port}')
            break

    if port == None:
        return

    while True:

        ser = serial.Serial(port.device, 128000, timeout=1)

        #Look for the response
        while 1:
            try:
                data = ser.read(1024)
            except:
                print('closing serial port')
                ser.close()
                break
            length = len(data)
            #print("recv", length, ": ", list(data))
            if(length > 0):         
                marshall(queue,data)
                time.sleep(0.001)
            
    logging.warning("IO Thread ended")
            
 # this is unused.   It was abandoned after moving to the Sense2Go as that module 
 # does not support the IFX ComLib interface.  Rather the marshalling was pushed
 # into the Sense2Go M0 MCU and we are now getting data from the serial interface.
            
def io_thread_socket_impl(readings):
    logging.warning("IO Thread started")

    while True:

        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_addr = '192.168.86.29'
        tcp_port = 8080
        

        # Connect the socket to the port where the server is listening
        server_address = (tcp_addr, tcp_port)
        print('connecting to {} port {}'.format(*server_address))
        try:
            sock.connect(server_address)
        except socket.error:
            print('error opening socket')
            sock.close()
            time.sleep(1)
            continue
    

        #Look for the response
        while 1:
            try:
                data = sock.recv(1024)
            except socket.error:
                print('closing socket')
                sock.close()
                break
            length = len(data)
            #print("recv", length, ": ", list(data))
            if(length > 0):         
                marshall(readings,data)
                time.sleep(0.001)
            else:
                sock.close()
                break
            
    logging.warning("IO Thread ended")
    
