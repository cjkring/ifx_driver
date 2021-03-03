import cv2
import numpy as np
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import queue
import math

def image_thread(conf,img_q):
    (h,w) = conf['app']['image_size'].split('x')
    h = int(h)
    w = int(w)
    videoStream = cv2.VideoCapture(0)
    while 1:
         cap,frame = videoStream.read()
         if( cap == True):
             img = np.fliplr(cv2.resize(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY),(h,w)))
             img_q.put(img)
             now = time.time()
             #print(f'now = {now}')
             # wake up at top of the current second
             time.sleep(math.ceil(now) - now)

def image_update_fig(n,img_q,im):

    if img_q.empty() == False:
        img = img_q.get()
        im.set_array(img)
    return im

if  __name__ == "__main__":
    import threading
    import config

    conf = config.read_config()
    config.validate_config(conf)

    img_q = queue.Queue(maxsize=2);

    image_t = threading.Thread(target=image_thread,args=(conf,img_q))
    image_t.start()

    fig = plt.figure()
    fig.set_size_inches(5,5)
    im_data = np.zeros((30,30),dtype=np.ubyte)
    im = plt.imshow(im_data, vmin=0, vmax=255, cmap='gray')

    anim = animation.FuncAnimation(fig,image_update_fig,fargs=(img_q,im),interval=100, blit=False)

    plt.show()