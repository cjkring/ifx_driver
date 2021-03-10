
import numpy as np
import json
import time
from annotations import getAnnotations

class Reading(dict):

    def __init__(self, seqno, count, data_i, data_q):
        global Annotations
        self['timestamp'] = time.time()
        self['seqno'] = seqno
        self['count'] = count
        self['data_i'] = np.asarray(data_i)
        self['data_q'] = np.asarray(data_q)
        #self['annotation'] = getAnnotations()['NONE']

class Readings:
    def __init__(self):
        self.head = -1
        self.size = 20000
        self.readings = np.empty(self.size, dtype=Reading)
        self.rgba = np.zeros((3,self.size,4),dtype=np.ubyte)
        self.pause = 0
    
    def __iter__(self):
        return iter(self.readings[:self.head + 1])

    def put(self,reading):
        while self.pause == 1:
            time.sleep(0.01)
        self.head += 1
        self.readings[self.head] = reading

    def get(self, index):
        while self.pause == 1:
            time.sleep(0.01)
        if index > self.head:
            return self.readings[self.head]
        if index < 0:
            return self.readings[0]
        return self.readings[index]
    
    def backup(self):
        self.pause = 1
        backup = Readings()
        tmp = self.readings
        self.readings = backup.readings
        backup.readings = tmp
        backup.head = self.head
        self.head = -1
        self.pause = 0
        return backup
