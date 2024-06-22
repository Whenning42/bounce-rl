# Call SetSpeedup() to change the time acceleration multiple for client programs
# listening on the given channel.

import posix
import struct

FIFO = "/tmp/time_control"
files = {}


def SetSpeedup(speedup, channel=""):
    global files
    speedup = float(speedup)
    # Opening the file for reading and writing prevents blocking until a reader opens
    # the file.
    if channel in files:
        f = files[channel]
    else:
        print("Writing time to file: ", FIFO + str(channel))
        f = posix.open(FIFO + str(channel), posix.O_RDWR | posix.O_CREAT)
        files[channel] = f
    posix.ftruncate(f, 0)
    SEEK_SET = 0
    posix.lseek(f, 0, SEEK_SET)
    posix.write(f, struct.pack("f", speedup))
