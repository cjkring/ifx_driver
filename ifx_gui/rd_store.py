
import numpy as np
import json
import time
from annotations import Annotations

#reading_size = 2 * 60 * 60  # store one hour of data
reading_size = 10000

class Reading(dict):

    def __init__(self, seqno, count, data_i, data_q):
        self['timestamp'] = time.time()
        self['seqno'] = seqno
        self['count'] = count
        self['data_i'] = np.asarray(data_i)
        self['data_q'] = np.asarray(data_q)
        self['annotation'] = Annotations.NONE

class Readings:
    def __init__(self):
        self.head = -1
        self.readings = np.empty(reading_size, dtype=Reading)
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
