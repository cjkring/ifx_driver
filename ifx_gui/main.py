# -*- coding: utf-8 -*-



"""
Created on Sun Dec  6 17:33:55 2020

@author: cjkri
"""

import threading
import queue
from iqplot import iqplot_thread_impl
from io_thread import io_thread_impl

    
if  __name__ == "__main__":
    q = queue.Queue(maxsize=1000)
    io = threading.Thread(target=io_thread_impl, args=(q,))
    iqplot = threading.Thread(target=iqplot_thread_impl, args=(q,))
    
    io.start()
    iqplot_thread_impl(q)
