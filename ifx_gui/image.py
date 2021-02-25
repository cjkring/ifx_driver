import cv2
import numpy as np
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation


fig = plt.figure()
im_data = np.zeros((640,480))
videoStream = cv2.VideoCapture(0)
cap,frame = videoStream.read()
print(f'cap: {cap}')
gray = cv2.cvtColor(cv2.resize(frame,(32,24)), cv2.COLOR_BGR2GRAY)
plt.imshow(gray, cmap='gray')
for w in (20,24,36,48,64):
    h = int(w * 1.5)
    print(f'generating test_{h}x{w}.png')
    img = cv2.cvtColor(cv2.resize(frame,(h,w)), cv2.COLOR_BGR2GRAY)
    cv2.imwrite(f'test_{h}x{w}.png', img)
plt.show()