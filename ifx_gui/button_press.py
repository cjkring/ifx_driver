import easygui

class ButtonPress(object):

    def __init__(self):
        self.indexFn = self.live_impl
        self.interval = 100
    
    def get_interval(self):
        if self.interval > 100:
            self.interval -= 100
        return self.interval

    # button press event handlers
    # the if logic in the button handlers makes it so if you click again on a button things stop

    def ff_prev(self, event):
        self.interval = 100
        if self.indexFn == self.ff_prev_impl:
            self.indexFn = self.stop_impl
        else:
            self.indexFn = self.ff_prev_impl

    def prev(self, event):
        self.interval = 500
        if self.indexFn == self.prev_impl:
            self.indexFn = self.stop_impl
        else:
            self.indexFn = self.prev_impl

    def stop(self, event):
        self.interval = 500
        self.indexFn = self.stop_impl

    def next(self, event):
        self.interval = 500
        if self.indexFn == self.next_impl:
            self.indexFn = self.stop_impl
        else:
            self.indexFn = self.next_impl

    def ff_next(self, event):
        self.interval = 100
        if self.indexFn == self.ff_next_impl:
            self.indexFn = self.stop_impl
        else:
            self.indexFn = self.ff_next_impl

    def live(self, event):
        self.interval = 100
        if self.indexFn == self.live_impl:
            self.indexFn = self.stop_impl
        else:
            self.indexFn = self.live_impl

    def load(self,event):
        file = easygui.fileopenbox()
        if file != None:
            print(f"load {file}")

    def save(self,event):
        file = easygui.filesavebox()
        if file != None:
            print(f"save {file}")

    # implementation of the index business logic

    def ff_prev_impl(self,cur_idx,readings):
        if cur_idx != None and cur_idx > 10:
            return cur_idx - 10
        return 0

    def prev_impl(self,cur_idx,readings):
        if cur_idx != None and cur_idx > 1:
            return cur_idx - 1
        return 0

    def stop_impl(self,cur_idx,readings):
        return cur_idx

    def next_impl(self,cur_idx,readings):
        if cur_idx != None and cur_idx < readings.head:
            return cur_idx + 1

    def ff_next_impl(self,cur_idx,readings):
        if cur_idx != None and cur_idx < readings.head - 10:
            return cur_idx + 10
        return readings.head

    def live_impl(self,cur_idx,readings):
        return readings.head
