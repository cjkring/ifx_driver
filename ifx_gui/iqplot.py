# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 14:56:54 2020

@author: cjkri
"""

# from matplotlib.mlab import window_hanning,specgram
from tkinter import Tk
#from tkinter.ttk import Tk
import matplotlib
#matplotlib.use('macosx') # dialog doesn't work
#matplotlib.use('tkagg') #dialog works, very slow on retina
#matplotlib.use('tkagg') #dialog works, very slow on retina
import matplotlib.pyplot as plt
import matplotlib.animation as animation
# from matplotlib.colors import LogNorm
import numpy as np
import logging
import time
from datetime import datetime
import math
import cmath
import threading
from io_thread import io_thread_impl
from backup_thread import backup_thread_impl
import bottleneck as bn
from matplotlib.widgets import Button, RadioButtons, TextBox, Slider
import rd_store
import button_press
from annotations import Annotations
from avro_export import avroImport, avroExport
numpoints = 256
anim = None

root = Tk()
root.withdraw


def iqplot_update_fig(n,  readings, buttons, scat, phase_plot, velocity_plot, unrolled_plot, mag_plot, seqno):

    # points come in FIFO order but we want to newest a the top of the array.
    # reading points into the array, then reversing the array and adding points from the 
    # previous data to keep the number of points constant

    # in case annotation button was pressed during the last frame
    # this is brute force and perhaps incorrect -- perhaps should be cached
    if buttons.annotation != Annotations.EXISTING:
        reading = readings.get(iqplot_update_fig.lastReading)
        reading['annotation'] = buttons.annotation
 
    idx = buttons.indexFn(iqplot_update_fig.lastReading,readings)

    # mechanism for forward / reverse to start slow then to speed up
    #anim.event_source.interval = buttons.get_interval()

    if idx == iqplot_update_fig.lastReading or idx == -1:
        # no new readings
        # TODO: don't return the entire list of artists
        time.sleep(0.01)
        return scat,phase_plot,velocity_plot,unrolled_plot,mag_plot,seqno
    try:
        #frame.set_val(idx)
        iqplot_update_fig.lastReading = idx
        reading = readings.get(iqplot_update_fig.lastReading)

        # annotation specified by radio button
        if buttons.annotation != Annotations.EXISTING:
            reading['annotation'] = buttons.annotation

        date_time = datetime.fromtimestamp(reading['timestamp'])
        seqno.set_text(f'frame: {idx}\ntime: {date_time}\nseqno: {reading["seqno"]}\nannotation: {reading["annotation"].value}')
        #seqno.set_val(reading.seqno)
        #timestamp.set_val(reading.timestamp)
        #packet = np.complex(reading["data_i"],reading["data_q"])
        packet = reading["data_i"] + reading["data_q"] * 1j
        #print(f'{reading["seqno"]},{reading["count"]},{packet[0]},{packet[-1]}')

        #iq plot
        scat.set_offsets( np.column_stack((reading["data_i"],reading["data_q"])))

        #phase plot
        magnitudes = np.absolute(packet)
        mag_plot.set_ydata(magnitudes)

        #phase plot
        phases = np.angle(packet)

        average = np.copy(phases)
        phase_plot.set_ydata(average)

        offset = 0
        last_v = 0
        threshold = np.pi * 0.8
        for i in range(len(phases)):
            v = phases[i]
            #print(f"offset = {offset}, v={v}. last_v = {last_v}")
            if v > threshold and last_v < -threshold:
                # negative rollover
                offset -= np.pi * 2
            elif v < -threshold and last_v > threshold:
                # negative rollover
                offset += np.pi * 2
            last_v = v
            phases[i] = v + offset

        unrolled_plot.set_ydata(phases)

        #phase velocity
        tmp1 = phases[:-1]
        tmp2 = phases[1:]
        velocity = np.subtract(tmp2,tmp1)
        pi_2 = np.pi / 2
        #velocity = np.subtract(phases[:-1], phases[1:])
        with np.nditer(velocity, op_flags=['readwrite']) as it:
            for v in it:
                if v < -pi_2:
                    tmp = v + np.pi
                    while tmp < -pi_2:
                        tmp += np.pi
                    v[...] = tmp
                elif v > pi_2:
                    tmp = v - np.pi
                    while tmp > pi_2:
                        tmp -= np.pi
                    v[...] = tmp
        tmp = bn.move_mean( velocity, window=5, min_count=1 )
        velocity_plot.set_ydata(tmp)


        return scat,phase_plot,velocity_plot,unrolled_plot,mag_plot,seqno
    except Exception as e:
        print(f'Unexpected error: {e}')
        return []


def iqplot_thread_impl(q):

    logging.warning("IQ Plot Thread started")
    fig = plt.figure()
    fig.set_size_inches(12,8)
    fig.subplots_adjust(bottom=0.2)

    bleft = 0.36
    bwidth = 0.05
    bbottom = 0.05
    bheight = 0.035
    bstep = 0.06

    buttons = button_press.ButtonPress()

    # axe_frame =  plt.axes([0.13, 0.1, 0.6, bheight])
    # frame =    Slider(axe_frame, 'Frame', 0, 10000,  valinit=0, valstep=1)
    # frame.on_changed(buttons.frame)
    #buttons.frame_slider = bframe

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
    
    blive =    Button(plt.axes([bleft + 5 * bstep, bbottom, bwidth, bheight]), 'live')
    blive.on_clicked(buttons.live)

    bexport = Button(plt.axes([bleft + 7 * bstep, bbottom, bwidth, bheight]), 'export')
    bexport.on_clicked(lambda x: buttons.save(readings))

    bimport = Button(plt.axes([bleft + 8 * bstep, bbottom, bwidth, bheight]), 'import')
    bimport.on_clicked(lambda x: buttons.load(readings))


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


    #seqno = ax6.text(0.0, 0.75, "frame:\ntime:\nseqno:\nannotation:", fontsize=10)
    ax7 = plt.axes([0.11,-0.16, 0.2,0.3])
    ax7.axis('off')
    seqno = ax7.text(0.0, 0.75, "frame:\ntime:\nseqno:\nannotation:", fontsize=10)

    global anim
    anim = animation.FuncAnimation(fig,iqplot_update_fig,fargs=(readings,buttons,scat,phase,velocity,unrolled,magnitude,seqno),interval=100, blit=True)
    plt.show()

iqplot_update_fig.lastReading = -2
if  __name__ == "__main__":
    readings = rd_store.Readings()
    io = threading.Thread(target=io_thread_impl, args=(readings,))
    io.start()
    backup = threading.Thread(target=backup_thread_impl, args=(readings,))
    backup.start()
    iqplot_thread_impl(readings)



