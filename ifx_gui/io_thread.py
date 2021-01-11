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


samples_per_packet = 256
#seek in data for DEADBEEF, then get 12 bytes of data after that.  Data can 
#spread across multiple data packets.
def marshall(queue,data):
    

    
    packet_len = samples_per_packet * 8 + 8 # has to match driver, include seqno and count
    i = 0;
    
    length = len(data)
    
    if marshall.looking == 1:
        # have found a DEADBEEF now looking for payload
        if(len(marshall.last) + len(data) >= packet_len):  
            # sufficient data - concat and parse
            i = packet_len - len(marshall.last)
            parse_data(queue,marshall.last + data[:i],1)
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
            i = i + 4;
           # print('i=',i,',len=',length)
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
                parse_data(queue,data[i:i+packet_len],2);
                i = i + packet_len;
                marshall.looking = 0
            
        else:
            i = i + 1;

def parse_data(queue,packet, loc):       

    #print("parsing: ",loc,',', list(packet))

    reading_array = np.empty(samples_per_packet, dtype=complex)

    (seqno, count) = unpack( '!II', packet[0:8] )
    if( seqno > parse_data.prev_seqno + 1 ):
        print("Corrupt data: ", packet)
    parse_data.prev_seqno = seqno
    for j in range( count ):
        idx = 8 + 8 * j
        (i,q) = unpack( '!II', packet[idx:idx+8] )

        I = (i - 100000 )/ 1000.0 ;
        Q = (q - 100000 )/ 1000.0 ;
        
        #print(count,',',I,',',Q)
    
        #reading = complex(I,Q)
        reading_array[j] = complex(I,Q)
        #reading_array[j] = I
        #print(reading)
    print(seqno,',',len(reading_array),',',reading_array[0],',',reading_array[-1])
    queue.put(reading_array)
        
           
                
marshall.looking = 0
marshall.last = b''
parse_data.prev_seqno = 0
            
            
def io_thread_impl(queue):
    logging.warning("IO Thread started")

    while True:

        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_addr = '172.24.80.1'
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
                marshall(queue,data)
                time.sleep(0.001)
            else:
                sock.close()
                break
            
    logging.warning("IO Thread ended")
    
