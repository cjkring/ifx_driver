
import numpy as np

reading_size = 2 * 60 * 60  # store one hour of data

class Reading:

    def __init__(self, seqno, count, data):
        self.seqno = seqno
        self.count = count
        self.data = data

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