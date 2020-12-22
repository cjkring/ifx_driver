# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 14:56:54 2020

@author: cjkri
"""

# from matplotlib.mlab import window_hanning,specgram
import matplotlib.pyplot as plt
import matplotlib.animation as animation
# from matplotlib.colors import LogNorm
import numpy as np
import logging
import queue
import time
import math
import cmath
import threading
from io_thread import io_thread_impl

numpoints = 512
offsets = np.zeros((numpoints,2))
def iqplot_update_fig(n,  q, scat):

    # points come in FIFO order but we want to newest a the top of the array.
    # reading points into the array, then reversing the array and adding points from the 
    # previous data to keep the number of points constant

    i = 0
    global offsets
    offsets = np.empty([numpoints,2])
    while(True):
        try:
            packet = q.get(block=False)
            for reading in packet:
                offsets[i] = [reading.real,reading.imag]
            #(r, theta) = cmath.polar(tmp)
            # i += 1
            # if i == numpoints:
            scat.set_offsets(offsets)
            time.sleep(0.025)
            
        except queue.Empty:
            return
 
 #everything below is now unused

    if i > 0:
        # tmp offsets are in reverse order 
        # np.flip(tmp_offsets,0)
        # offsets = np.concatenate((tmp_offsets[:i:-1], offsets[:-i]))
        # we want at most numpoints in the updated offset


        rows_dropped = len(offsets) + i - numpoints
        #print("offsets = ", len(offsets)," i = ", i, "rows_dropped = ", rows_dropped)
        #tmp = tmp_offsets[0:i]
        new_offsets = np.flip(tmp_offsets[0:i])
        if( rows_dropped > 0 ):
            offsets = np.concatenate((new_offsets,offsets[:-rows_dropped]))
        else:
            offsets = np.concatenate((new_offsets,offsets))

        # print("new", new_offsets[:,0])
        # print("offsets", offsets[:,0])
        scat.set_offsets(offsets)



def iqplot_thread_impl(q):

    logging.warning("IQ Plot Thread started")
    fig = plt.figure()
    fig.set_size_inches(4,4)
    
    colors = np.array(range(0,numpoints))

    ax1 = fig.add_subplot(111)
    scat = ax1.scatter(offsets[:,0], offsets[:,1], c=colors, cmap='plasma', alpha=0.75)
    ax1.set_xlim(-5,5)
    ax1.set_ylim(-5,5)
    ax1.set_xlabel('I')
    ax1.set_ylabel('Q')
    ax1.set_title('I/Q Readings')
    anim = animation.FuncAnimation(fig,iqplot_update_fig,fargs=(q,scat),interval=200, blit=False)
    plt.show()

if  __name__ == "__main__":
    q = queue.Queue(maxsize=1000)
    io = threading.Thread(target=io_thread_impl, args=(q,))
   # iqplot = threading.Thread(target=iqplot_thread_impl, args=(q,))
    
    io.start()
    iqplot_thread_impl(q)


