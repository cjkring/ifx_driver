# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 13:34:50 2020

@author: cjkri


"""
############### Import Libraries ###############
from matplotlib.mlab import window_hanning,specgram
from numpy.fft import fft
from numpy import hanning
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LogNorm
import numpy as np
import logging
import queue
import threading
from io_thread import io_thread_impl



############### Constants ###############
#SAMPLES_PER_FRAME = 10 #Number of mic reads concatenated within a single window
# SAMPLES_PER_FRAME = 1
#nfft = 1024#256#1024 #NFFT value for spectrogram
#overlap = 1000#512 #overlap value for spectrogram
#rate = mic_read.RATE #sampling rate
frequency_step = 1
frequency_count = 128
bin_count = 200



############### Functions ###############

def get_sample(stream,pa):
    data = mic_read.get_data(stream,pa)
    return data

#def get_specgram(q):
    # arr2D,freqs,bins = specgram(signal,window=window_hanning,
    #                             Fs = rate,NFFT=nfft,noverlap=overlap)
    #bins = np.arange(201)              
    # arr2D = np.random.rand(frequency_count)                          
    # return arr2D


def update_fig(n,im,im_data,q):
   # global im_data

    # data = get_sample(stream,pa)
    # data = 0
    # rate = 0
    # arr2D = get_specgram(datrate)
    try:
        packet = q.get(block=False)   
    except queue.Empty:
        return
    sample = packet * hanning(256)
    fft_out = fft(sample)
    fft_prep = np.abs(fft_out) / 500
    #tmp3 = ( frequency_count // 2 ) + 1
    #tmp2 = fft_prep[1:tmp3]
    #tmp1 = , fft_prep[tmp3:1:-1]
    #fft_final = np.append(tmp1,tmp2)
    fft_final = fft_prep[1:frequency_count+1] + fft_prep[:-frequency_count-1:-1]
    print(f'fft_final min={fft_final.min()}, max = {fft_final.max()}')

    # for visualization, only l

    # the oldest column of imdata is removed and a new column is added
    # this is performed by shifting the columns along the x axis then adding a column
    for i in range(bin_count - 1 ):
        im_data[i] = im_data[i+1]
    im_data[bin_count - 1] = fft_final

    im.set_array(im_data.transpose())
    return im



def spectogram_thread_impl(q):
    # plot initialization
    fig = plt.figure()
    im_data = np.zeros(( bin_count, frequency_count))
   
    extent = (0,bin_count,0,frequency_count)
    im = plt.imshow(im_data.transpose(),aspect='auto',extent = extent,interpolation="none", origin='lower',
                    cmap = 'jet',norm = LogNorm(vmin=.5,vmax=500))
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Real Time Spectogram')

    # animation
    anim = animation.FuncAnimation(fig,update_fig,fargs=(im,im_data,q), blit = False, interval=100)
                                
    try:
        plt.show()
    except:
        print("Plot Closed")

    
if  __name__ == "__main__":
    q = queue.Queue(maxsize=1000)
    io = threading.Thread(target=io_thread_impl, args=(q,))
    
    io.start()
    spectogram_thread_impl(q)
