#import easygui
from annotations import Annotations
from tkinter.filedialog import askopenfilename, asksaveasfilename
from avro_export import avroExport, avroImport
from time import time_ns
class ButtonPress(object):
    def __init__(self):
        self.indexFn = self.live_impl
        self.interval = 200
        self.frame_incr = 1
        self.last_update = 0
        self.annotation = Annotations.NONE
        self.annotateButton = None
    
    
    #def get_interval(self):
    #    return self.interval

    # annotation radio button
    def annotate(self, event):
        self.annotation = Annotations(event)
        print(f'setting annotation to {self.annotation}')

    # frame slider
    def frame(self, event):
        self.interval = 200000000

    # frame press event handlers

    def ff_prev(self, event):
        self.setAnnotationsExisting()
        self.interval = 100000000
        self.toggle_speed(self.next_impl, -1, -10)

    def prev(self, event):
        #self.setAnnotationsExisting()
        self.interval = 500000000
        self.frame_incr = -1
        self.toggle_impl(self.next_impl)

    def stop(self, event):
        self.setAnnotationsExisting()
        self.interval = 500000000
        self.indexFn = self.stop_impl

    def next(self, event):
        #self.setAnnotationsExisting()
        self.interval = 500000000
        self.frame_incr = 1
        self.toggle_impl(self.next_impl)

    def ff_next(self, event):
        self.setAnnotationsExisting()
        self.interval = 100000000
        self.toggle_speed(self.next_impl, 1, 10)

    def live(self, event):
        self.setAnnotationsExisting()
        self.interval = 100000000
        self.toggle_impl(self.live_impl)

    # turns annotations back to existing when a speed button is pressed
    def setAnnotationsExisting(self):
        self.annotation = Annotations.EXISTING
        self.annotateButton.set_active(0)

    # when you click on a ff button you switch beween fast and really fast
    def toggle_speed(self, indexFn, slow, fast):
        if self.indexFn != indexFn:
            self.indexFn = indexFn
            self.frame_incr = slow
        elif self.frame_incr == slow:
            self.frame_incr = fast
        else:
            self.frame_incr = slow

    # when you click on a button you switch beween pause and move
    def toggle_impl(self, indexFn):
        if self.indexFn == indexFn:
            self.indexFn = self.stop_impl
        else:
            self.indexFn = indexFn

    def stop_impl(self,frame_idx,readings):
        return frame_idx

    def next_impl(self,frame_idx,readings):
        now = time_ns()
        if self.last_update + self.interval > now:
            return frame_idx
        self.last_update = now
        next_idx = frame_idx + self.frame_incr
        if next_idx < 0:
            next_idx = 0
        if next_idx > readings.head:
            next_idx = readings.head

        return next_idx

    def live_impl(self,frame_idx,readings):
        return readings.head


    # def load(self,event):
    #     file = askopenfilename()
    #     #file = easygui.fileopenbox()
    #     if file != None:
    #         print(f"load {file}")

    # def save(self,event):
    #     #file = askopenfilename()
    #     if file != None:
    #         print(f"save {file}")

    def save(self,readings):
        self.indexFn = self.stop_impl
        filename = asksaveasfilename()
        print(f'export: {filename}')
        avroExport(filename, readings)

    def load(self,readings):
        self.indexFn = self.stop_impl
        filename = askopenfilename()
        print(f'import: {filename}')
        avroImport(filename, readings)
