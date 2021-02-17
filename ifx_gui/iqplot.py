# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 14:56:54 2020

@author: cjkri
"""

from tkinter import Tk
#from matplotlib.backends.backend_tkagg import (
#    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
#from matplotlib.backend_bases import key_press_handler

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
from frame_process import process_frame

import numpy as np
import logging
import time
from datetime import datetime
import math
import cmath
import threading
from io_thread import io_thread_impl
from backup_thread import backup_thread_impl
from matplotlib.widgets import Button, RadioButtons, TextBox, Slider
import rd_store
import button_press
from annotations import Annotations
from avro_export import avroImport, avroExport
from config import read_config
numpoints = 256
video_frames = 50
anim = None

# business logic for what rbga frames to show
def calc_window(idx,window_size,readings):
    
    if idx < window_size:
        return 0,window_size

    idx_min = int(idx - window_size / 2)
    idx_max = int(idx + window_size / 2)

    if idx_max >= readings.head:
        return readings.head - window_size,readings.head + 1

    return idx_min,idx_max

def iqplot_update_fig(n,  readings, buttons, scat, phase_plot, velocity_plot, unrolled_plot, mag_plot, seqno, video):

    # points come in FIFO order but we want to newest a the top of the array.
    # reading points into the array, then reversing the array and adding points from the 
    # previous data to keep the number of points constant

    # in case annotation button was pressed during the last frame
    # this is brute force and perhaps incorrect -- perhaps should be cached
    if buttons.annotation != Annotations.EXISTING:
        reading = readings.get(iqplot_update_fig.lastReading)
        reading['annotation'] = buttons.annotation
 
    if iqplot_update_fig.lastReading == None or iqplot_update_fig.lastReading > readings.head:
        # caused by Avro load
        idx = 0
    else:
        idx = buttons.indexFn(iqplot_update_fig.lastReading,readings)

    if idx == iqplot_update_fig.lastReading or idx == -1:
        # no new readings
        # TODO: don't return the entire list of artists
        iqplot_update_fig.lastReading = idx
        time.sleep(0.1)
        return scat,phase_plot,velocity_plot,unrolled_plot,mag_plot,seqno, video
    try:
        
        # the transparency of the current frame is 255, other frames are lower
        if iqplot_update_fig.lastReading != None:
            readings.rgba[0,iqplot_update_fig.lastReading,3] = 0
        readings.rgba[0,idx,3] = 100

        iqplot_update_fig.lastReading = idx
        reading = readings.get(iqplot_update_fig.lastReading)

        # annotation specified by radio button
        if buttons.annotation != Annotations.EXISTING:
            reading['annotation'] = buttons.annotation

        date_time = datetime.fromtimestamp(reading['timestamp'])
        seqno.set_text(f'frame: {idx}\ntime: {date_time}\nseqno: {reading["seqno"]}\nannotation: {reading["annotation"].value}')
        #print(f'{reading["seqno"]},{reading["count"]},{packet[0]},{packet[-1]}')

        #iq plot
        scat.set_offsets( np.column_stack((reading["data_i"],reading["data_q"])))

        if hasattr(reading, "magnitudes") == False:
            process_frame(readings, idx, reading)
     
        #magnitude plot
        mag_plot.set_ydata(reading.magnitudes)

        #phase plots
        phase_plot.set_ydata(reading.phases)
        unrolled_plot.set_ydata(reading.phases_unrolled)
        velocity_plot.set_ydata(reading.phase_velocity)

        # setting range for video
        (idx_min,idx_max) = calc_window(idx,video_frames,readings)
        video.set_array(readings.rgba[:,idx_min:idx_max,:])

        return scat,phase_plot,velocity_plot,unrolled_plot,mag_plot,seqno, video
    except Exception as e:
        print(f'Unexpected error: {e}')
        return []


def iqplot_thread_impl(readings,config):

    # this produces a dangling root window but is needed for the filesaveas dialogs to work
    Tk() 
    logging.warning("IQ Plot Thread started")
    fig = plt.figure()
    fig.set_size_inches(12,8)
    fig.subplots_adjust(bottom=0.3)

    #canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.

    bleft = 0.36
    bwidth = 0.05
    bbottom = 0.05
    bheight = 0.035
    bstep = 0.06

    buttons = button_press.ButtonPress()

    bff_prev = Button( plt.axes([bleft, bbottom, bwidth, bheight]), '<<')
    bff_prev.on_clicked(buttons.ff_prev)

    bprev =  Button(plt.axes([bleft + bstep, bbottom, bwidth, bheight]), '<')
    bprev.on_clicked(buttons.prev)
    
    bstop =  Button(plt.axes([bleft + 2 * bstep, bbottom, bwidth, bheight]), '||')
    bstop.on_clicked(buttons.stop)
    
    bnext =  Button(plt.axes([bleft + 3 * bstep, bbottom, bwidth, bheight]), '>')
    bnext.on_clicked(buttons.next)
    
    bff_next =    Button(plt.axes([bleft + 4 * bstep, bbottom, bwidth, bheight]), '>>')
    bff_next.on_clicked(buttons.ff_next)
    
    blast =    Button(plt.axes([bleft + 5 * bstep, bbottom, bwidth, bheight]), 'last')
    blast.on_clicked(buttons.last)

    bload = Button(plt.axes([bleft + 7 * bstep, bbottom, bwidth, bheight]), 'load')
    bload.on_clicked(lambda x: buttons.load(config,readings))
    buttons.importbutton = bload

    bsave = Button(plt.axes([bleft + 8 * bstep, bbottom, bwidth, bheight]), 'save')
    bsave.on_clicked(lambda x: buttons.save(config,readings))
    buttons.savebutton = bsave

    offsets = np.zeros(numpoints)
    
    colors = np.array(range(0,numpoints))

    ax1 = fig.add_subplot(231)
    scat = ax1.scatter(offsets, offsets, c=colors, cmap='plasma', alpha=0.75)
    ax1.set_xlim(-3000,3000)
    ax1.set_ylim(-3000,3000)
    ax1.set_title('I/Q Readings')

    ax2 = fig.add_subplot(235)
    ax2.set_ylim(-np.pi * 1.5,np.pi * 1.5)
    ax2.set_xlim(0,255)
    ax2.set_title('phase')
    ax2.axhline(0,color='grey')
    phase, = ax2.plot(offsets)

    ax3 = fig.add_subplot(234)
    ax3.set_ylim(-np.pi/2,np.pi/2)
    ax3.set_xlim(0,254)
    ax3.set_title('phase velocity')
    ax3.axhline(0,color='grey')
    velocity, = ax3.plot(offsets[:-1])

    ax4 = fig.add_subplot(236)
    ax4.set_ylim(-np.pi * 10 ,np.pi * 10 )
    ax4.set_xlim(0,256)
    ax4.set_title('phase no rollover')
    ax4.axhline(0,color='grey')
    unrolled, = ax4.plot(offsets)

    ax5 = fig.add_subplot(232)
    ax5.set_ylim(0 ,2000 )
    ax5.set_xlim(0,252)
    ax5.set_title('magnitude')
    ax5.axhline(0,color='grey')
    magnitude, = ax5.plot(offsets)

    ax6 = fig.add_subplot(233)
    ax6.axis('off')

    labels = [anno.value for anno in Annotations]
    bannotate = RadioButtons(ax6,labels, active=None)
    bannotate.on_clicked(buttons.annotate)
    bannotate.set_active(0)
    buttons.annotateButton = bannotate

    ax8 = plt.axes([0.15,0.18, 0.7,0.05])
    ax8.axis('off')
    tmp = readings.rgba[:,0:video_frames,:]
    video = ax8.imshow(tmp, vmin=0, vmax=255, aspect='auto')

    ax7 = plt.axes([0.11,-0.16, 0.2,0.3])
    ax7.axis('off')
    seqno = ax7.text(0.0, 0.75, "frame:\ntime:\nseqno:\nannotation:", fontsize=10)

    global anim
    anim = animation.FuncAnimation(fig,iqplot_update_fig,fargs=(readings,buttons,scat,phase,velocity,unrolled,magnitude,seqno,video),interval=100, blit=True)
    plt.show()
    #canvas.draw()

iqplot_update_fig.lastReading = None
if  __name__ == "__main__":
    config = read_config()
    readings = rd_store.Readings()
    io = threading.Thread(target=io_thread_impl, args=(readings,))
    io.start()
    backup = threading.Thread(target=backup_thread_impl, args=(readings,config))
    backup.start()
    iqplot_thread_impl(readings,config)



