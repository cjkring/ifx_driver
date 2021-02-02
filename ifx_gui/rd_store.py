
import numpy as np
import json
import time
from annotations import Annotations

reading_size = 2 * 60 * 60  # store one hour of data

class Reading:

    def __init__(self, seqno, count, data):
        self.timestamp = time.time()
        self.seqno = seqno
        self.count = count
        self.data = data
        self.annotation = Annotations.NONE

class Readings:

    def __init__(self):
        self.head = -1
        self.readings = np.empty(reading_size, dtype=Reading)

    def put(self,reading):
        self.head += 1
        self.readings[self.head] = reading

    def get(self, index):
        if index > self.head:
            return self.readings[self.head]
        if index < 0:
            return self.readings[0]
        return self.readings[index]
    
    def write(self, filename):
        print(f'Write {filename}')

    def read(self, filename):
        print(f'Read {filename}')

def saveFile(filename):
    if filename == None:
        print(f"save: no file specified")
        return
    print(f"save:{filename}")

def loadFile(filename):
    if filename == None:
        print(f"load: no file specified")
        return
    print(f"load:{filename}")
    
    