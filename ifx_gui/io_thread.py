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
from frame_process import process_frame


samples_per_packet = 256
#seek in data for DEADBEEF, then get 12 bytes of data after that.  Data can 
#spread across multiple data packets.
def marshall(reading_q,data):
    

    
    packet_len = samples_per_packet * 4 + 4 # has to match driver, include seqno and count
    i = 0
    
    length = len(data)
    
    if marshall.looking == 1:
        # have found a DEADBEEF now looking for payload
        if(len(marshall.last) + len(data) >= packet_len):  
            # sufficient data - concat and parse
            i = packet_len - len(marshall.last)
            parse_data(reading_q, marshall.last + data[:i],1)
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
                parse_data(reading_q, data[i:i+packet_len],2)
                i = i + packet_len
                marshall.looking = 0
            
        else:
            i = i + 1

def parse_data(reading_q, packet,loc):       

    #print("parsing: ",loc,',', list(packet))

    data_i = np.empty(samples_per_packet, dtype=np.int16)
    data_q = np.empty(samples_per_packet, dtype=np.int16)

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
            data_i[j] = int(I - parse_data.avg_i)
            data_q[j] = int(Q - parse_data.avg_q)

            #print(reading)
        #print(loc,',',seqno,',',len(reading_array),',',reading_array[0],',',reading_array[-1])

        reading = rd_store.Reading(seqno,count,data_i,data_q)
        process_frame(reading)
        reading_q.put(reading)
    except Exception as e:
        print(f'parsing exception: dropping packet after {seqno}:{e}')
        return

parse_data.avg_count = 0
parse_data.sum_i = 0
parse_data.sum_q = 0
parse_data.avg_i = 0
parse_data.avg_q = 0
        
           
marshall.looking = 0
marshall.last = b''
parse_data.prev_seqno = 0

# this is the interface to the Sense2Go module via a USB CDC serial port

def io_thread_impl(reading_q):
    logging.warning("IO Thread started")
    io_thread_impl.keep_running = True

    
    foundPort = False
    while foundPort is False:
        port = None
        for p in serial.tools.list_ports.comports():
            if p.vid == 4966 and p.pid == 261:
                port = p
                foundPort = True
                print(f'Found: {port}')
                break

        if foundPort == False:
            time.sleep(1)

    first = True
    while True:
        if io_thread_impl.keep_running:
            try:
                ser = serial.Serial(port.device, 128000, timeout=1)
                first = True

                #Look for the response
                while io_thread_impl.keep_running:
                    try:
                        data = ser.read(1024)
                        length = len(data)
                        #print("recv", length, ": ", list(data))
                        if(length > 0):         
                            marshall(reading_q, data)
                            #time.sleep(0.001)
                    except:
                        print('closing serial port')
                        ser.close()
                        break
            except Exception as e:
                if first:
                    print(f'io_thread: Cannot open serial port: {e}')
                first = False
                time.sleep(1)
        else:
            time.sleep(1)
                
    logging.warning("IO Thread ended")

def io_thread_lock(value):
    if value == True:
        io_thread_impl.keep_running = False
        #keep_running.acquire()
    else:
        io_thread_impl.keep_running = True
        #keep_running.release()
            
            
 # this is unused.   It was abandoned after moving to the Sense2Go as that module 
 # does not support the IFX ComLib interface.  Rather the marshalling was pushed
 # into the Sense2Go M0 MCU and we are now getting data from the serial interface.

def io_thread_socket_impl(reading_q):
    logging.warning("IO Thread started")

    keep_running = 1



    while 1:
        while keep_running:

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
                time.sleep(0.5)
                continue
        
    
            #Look for the response
            while keep_running:
                try:
                    data = sock.recv(1024)
                except socket.error:
                    print('closing socket')
                    sock.close()
                    break
                length = len(data)
                #print("recv", length, ": ", list(data))
                if(length > 0):         
                    marshall(reading_q,data)
                    time.sleep(0.001)
                else:
                    sock.close()
                    break
    # sleep to keep from pegging the CPU if keep_running == False
    time.sleep(0.1)
                
    logging.warning("IO Thread ended")

if  __name__ == "__main__":
    #import threading
    import queue
    io_thread_impl(queue.Queue(maxsize=10000))