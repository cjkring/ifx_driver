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
from frame_process import frame_rgba
import multiprocessing as mp

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
from annotations import getAnnotations, addToAnnotations
from avro_export import avroImport, avroExport
from config import read_config, validate_config
from queue import Queue
from image import image_thread
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

def iqplot_update_fig(n,  readings, reading_q, img_q, buttons, scat, phase_plot, velocity_plot, unrolled_plot, mag_plot, seqno, video, image):

    # readings are pushed to reading_q by the io_thread Process.

    # TODO: this probably breaks due to avro load.  Sort out later....
    while reading_q.empty() == False:
        reading = reading_q.get()
        readings.put(reading)
        frame_rgba(readings, readings.head, reading)
        reading['annotation'] = getAnnotations().NONE
        if img_q.empty() == False:
            reading['image'] = img_q.get()
        else: 
            reading['image'] = None

 
    if iqplot_update_fig.lastReading == None or iqplot_update_fig.lastReading > readings.head:
        # caused by Avro load
        idx = 0
    else:

        # in case annotation button was pressed during the last frame
        # this is brute force and perhaps incorrect -- perhaps should be cached
        if buttons.annotation != getAnnotations().EXISTING:
            reading = readings.get(iqplot_update_fig.lastReading)
            reading['annotation'] = buttons.annotation

        idx = buttons.indexFn(iqplot_update_fig.lastReading,readings)

    if idx == iqplot_update_fig.lastReading or idx == -1:
        # no new readings
        # TODO: don't return the entire list of artists
        iqplot_update_fig.lastReading = idx
        time.sleep(0.1)
        return scat,phase_plot,velocity_plot,unrolled_plot,mag_plot,seqno, video, image
    try:
        
        # the transparency of the current frame is 255, other frames are lower
        if iqplot_update_fig.lastReading != None:
            readings.rgba[0,iqplot_update_fig.lastReading,3] = 0
        readings.rgba[0,idx,3] = 100

        iqplot_update_fig.lastReading = idx
        reading = readings.get(iqplot_update_fig.lastReading)

        # annotation specified by radio button
        if buttons.annotation != getAnnotations().EXISTING:
            reading['annotation'] = buttons.annotation

        date_time = datetime.fromtimestamp(reading['timestamp'])
        seqno.set_text(f'frame: {idx}\ntime: {date_time}\nseqno: {reading["seqno"]}\nannotation: {reading["annotation"].name}')
        #print(f'{reading["seqno"]},{reading["count"]},{packet[0]},{packet[-1]}')

        #iq plot
        scat.set_offsets( np.column_stack((reading["data_i"],reading["data_q"])))

        # if hasattr(reading, "magnitude") == False:
        #     process_frame(readings, idx, reading)
     
        #magnitude plot
        mag_plot.set_ydata(reading['magnitude'])

        #phase plots
        phase_plot.set_ydata(reading['phase'])
        unrolled_plot.set_ydata(reading['phase_unrolled'])
        velocity_plot.set_ydata(reading['phase_velocity'])

        # setting range for video
        (idx_min,idx_max) = calc_window(idx,video_frames,readings)
        video.set_array(readings.rgba[:,idx_min:idx_max,:])

        #image
        img = reading['image']
        if img is not None:
            image.set_array(img)

        return scat,phase_plot,velocity_plot,unrolled_plot,mag_plot,seqno, video, image
    except Exception as e:
        print(f'iqplot_update_fig: {e}')
        return []

    
def createRadioButton(ax,buttons):
    labels = [anno.name for anno in getAnnotations()]
    bannotate = RadioButtons(ax,labels, active=None)
    bannotate.on_clicked(buttons.annotate)
    bannotate.set_active(0)
    buttons.annotateButton = bannotate

def iqplot_thread_impl(readings,config,reading_q, img_q):

    # this produces a dangling root window but is needed for the filesaveas dialogs to work
    Tk()  
    logging.warning("IQ Plot Thread started")
    fig = plt.figure()
    fig.set_size_inches(12,8)
    gridsize = (30,40)

    buttons = button_press.ButtonPress()
    offsets = np.zeros(numpoints)
    
    colors = np.array(range(0,numpoints))

    # I/Q readings
    ax = plt.subplot2grid(gridsize,(0,0),rowspan=9,colspan=10)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlim(-3000,3000)
    ax.set_ylim(-3000,3000)
    scat = ax.scatter(offsets, offsets, c=colors, cmap='plasma', alpha=0.75)
    ax.set_title('I/Q Readings')

    # phase
    ax = plt.subplot2grid(gridsize,(10,10),rowspan=9,colspan=10)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_ylim(-np.pi * 1.5,np.pi * 1.5)
    ax.set_xlim(0,255)
    ax.axhline(0,color='grey')
    phase, = ax.plot(offsets)
    ax.set_title('phase')

    # phase velocity
    ax = plt.subplot2grid(gridsize,(10,0),rowspan=9,colspan=10)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_ylim(-np.pi/2,np.pi/2)
    ax.set_xlim(0,254)
    ax.axhline(0,color='grey')
    velocity, = ax.plot(offsets[:-1])
    ax.set_title('phase velocity')

    # phase unrolled
    ax = plt.subplot2grid(gridsize,(10,20),rowspan=9,colspan=10)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_ylim(-np.pi * 10 ,np.pi * 10 )
    ax.set_xlim(0,256)
    ax.axhline(0,color='grey')
    unrolled, = ax.plot(offsets)
    ax.set_title('phase no rollover')

    # magnitude
    ax = plt.subplot2grid(gridsize,(0,10),rowspan=9,colspan=10)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_ylim(0 ,2000 )
    ax.set_xlim(0,252)
    ax.set_title('magnitude')
    ax.axhline(0,color='grey')
    magnitude, = ax.plot(offsets)

    # image 
    ax = plt.subplot2grid(gridsize,(0,20),rowspan=9,colspan=10)
    ax.axis('off')
    ax.set_title('image')
    im_data = np.random.randint(230,255,(30,30),dtype=np.ubyte)
    image = ax.imshow(im_data, vmin=0, vmax=255, cmap='gray')

    # annotations buttons
    ax = plt.subplot2grid(gridsize,(0,30),rowspan=18,colspan=10)
    ax.set_title('annotations')
    createRadioButton(ax,buttons)

    ax = plt.subplot2grid(gridsize,(18,30),rowspan=1,colspan=10)
    text_box = TextBox(ax,None)
    text_box.on_submit(buttons.addAnnotation)
    buttons.anno_textbox = text_box


    # rgb hostory
    ax = plt.subplot2grid(gridsize,(20,0),rowspan=3,colspan=40)
    ax.axis('off')
    tmp = readings.rgba[:,0:video_frames,:]
    video = ax.imshow(tmp, vmin=0, vmax=255, aspect='auto')

    # info text
    ax = plt.subplot2grid(gridsize,(24,0),rowspan=5,colspan=15)
    ax.axis('off')
    seqno = ax.text(0, 0, "frame:\ntime:\nseqno:\nannotation:", fontsize=10)

    # control buttons
    bff_prev = Button( plt.subplot2grid(gridsize,(24,16),rowspan=2,colspan=3), '<<')
    bff_prev.on_clicked(buttons.ff_prev)

    bprev =  Button( plt.subplot2grid(gridsize,(24,20),rowspan=2,colspan=3), '<')
    bprev.on_clicked(buttons.prev)
    
    bstop =  Button( plt.subplot2grid(gridsize,(24,24),rowspan=2,colspan=3), '||')
    bstop.on_clicked(buttons.stop)
    
    bnext = Button( plt.subplot2grid(gridsize,(24,28),rowspan=2,colspan=3), '>')
    bnext.on_clicked(buttons.next)
    
    bff_next = Button( plt.subplot2grid(gridsize,(24,32),rowspan=2,colspan=3), '>>')
    bff_next.on_clicked(buttons.ff_next)
    
    blast = Button( plt.subplot2grid(gridsize,(24,36),rowspan=2,colspan=3), 'last')
    blast.on_clicked(buttons.last)

    bload = Button( plt.subplot2grid(gridsize,(27,22),rowspan=2,colspan=3), 'load')
    bload.on_clicked(lambda x: buttons.load(config,readings))
    buttons.importbutton = bload

    bsave = Button( plt.subplot2grid(gridsize,(27,26),rowspan=2,colspan=3), 'save')
    bsave.on_clicked(lambda x: buttons.save(config,readings))
    buttons.savebutton = bsave

    bexport = Button( plt.subplot2grid(gridsize,(27,30),rowspan=2,colspan=3), 'export')
    bexport.on_clicked(lambda x: buttons.export(config,readings))
    buttons.exportbutton = bexport


    global anim
    anim = animation.FuncAnimation(fig,iqplot_update_fig,fargs=(readings,reading_q, img_q, buttons,scat,phase,velocity,unrolled,magnitude,seqno,video,image),interval=100, blit=True)
    #plt.tight_layout()
    plt.show()
    #canvas.draw()

iqplot_update_fig.lastReading = None
if  __name__ == "__main__":

    config = read_config()
    validate_config(config)
    addToAnnotations(config['app']['annotations'])
    readings = rd_store.Readings()

    img_q = mp.Queue(maxsize=2);
    reading_q = mp.Queue(maxsize=2);

    image_t = mp.Process(target=image_thread,args=(config,img_q))
    image_t.start()

    io = mp.Process(target=io_thread_impl, args=(reading_q,))
    io.start()

    # this has to be a thread because it relies on readings
    # if this becomes an issue it can put checked and implemented from the iq_thread
    backup = threading.Thread(target=backup_thread_impl, args=(readings,config))
    backup.start()
    iqplot_thread_impl(readings,config,reading_q, img_q)



