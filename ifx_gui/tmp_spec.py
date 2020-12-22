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

numpoints = 100
offsets = np.zeros((numpoints,2))
def iqplot_update_fig(n,  q, scat):

    # points come in FIFO order but we want to newest a the top of the array.
    # reading points into the array, then reversing the array and adding points from the 
    # previous data to keep the number of points constant

    i = 0
    global offsets
    tmp_offsets = np.empty([numpoints,2])
    while(True):
        try:
            tmp = q.get(block=False)
            tmp_offsets[i] = [tmp.real,tmp.imag]
            #(r, theta) = cmath.polar(tmp)
            i += 1
            if i == numpoints:
                break
            
        except queue.Empty:
            break
 

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



def spec_thread_impl(q):

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
    anim = animation.FuncAnimation(fig,spec_update_fig,fargs=(q,scat),interval=200, blit=False)
    plt.show()

if  __name__ == "__main__":
    q = queue.Queue(maxsize=1000)
    io = threading.Thread(target=io_thread_impl, args=(q,))
    iqplot = threading.Thread(target=spec_thread_impl, args=(q,))
    
    io.start()
    spec_thread_impl(q)
    
############### Constants ###############
#SAMPLES_PER_FRAME = 10 #Number of mic reads concatenated within a single window
SAMPLES_PER_FRAME = 4
nfft = 1024#256#1024 #NFFT value for spectrogram
overlap = 1000#512 #overlap value for spectrogram
#rate = mic_read.RATE #sampling rate

############### Functions ###############
"""
get_sample:
gets the audio data from the microphone
inputs: audio stream and PyAudio object
outputs: int16 array
"""
def get_sample(stream,pa):
    data = mic_read.get_data(stream,pa)
    return data
"""
get_specgram:
takes the FFT to create a spectrogram of the given audio signal
input: audio signal, sampling rate
output: 2D Spectrogram Array, Frequency Array, Bin Array
see matplotlib.mlab.specgram documentation for help
"""
def get_specgram(signal,rate):
    arr2D,freqs,bins = specgram(signal,window=window_hanning,
                                Fs = rate,NFFT=nfft,noverlap=overlap)
    return arr2D,freqs,bins

"""
update_fig:
updates the image, just adds on samples at the start until the maximum size is
reached, at which point it 'scrolls' horizontally by determining how much of the
data needs to stay, shifting it left, and appending the new data. 
inputs: iteration number
outputs: updated image
"""
def update_fig(n):
    data = get_sample(stream,pa)
    arr2D,freqs,bins = get_specgram(data,rate)
    im_data = im.get_array()
    if n < SAMPLES_PER_FRAME:
        im_data = np.hstack((im_data,arr2D))
        im.set_array(im_data)
    else:
        keep_block = arr2D.shape[1]*(SAMPLES_PER_FRAME - 1)
        im_data = np.delete(im_data,np.s_[:-keep_block],1)
        im_data = np.hstack((im_data,arr2D))
        im.set_array(im_data)
    return im,