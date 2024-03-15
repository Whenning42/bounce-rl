import os
import signal

from Xlib import display

ds = []
for i in range(10):
    ds.append(display.Display())
os.kill(os.getpid(), signal.SIGKILL)
