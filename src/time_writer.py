# Call SetSpeedup() to change the time acceleration multiple for client programs listening on
# the given channel.

import subprocess
import time
import struct
import posix

FIFO = "/tmp/time_control"
f = None

def SetSpeedup(speedup, channel = ""):
    global f
    speedup = float(speedup)
    # Opening the file for reading and writing prevents blocking until a reader opens the file.
    if f is None:
        print("Writing time to file: ", FIFO + str(channel))
        f = posix.open(FIFO + str(channel), posix.O_RDWR | posix.O_CREAT)
    posix.ftruncate(f, 0)
    SEEK_SET = 0
    posix.lseek(f, 0, SEEK_SET)
    posix.write(f, struct.pack("f", speedup))

if __name__ == "__main__":
    for speedup, channel in [(12, 0), (18, 1)]:
        SetSpeedup(speedup, channel)
        environment = {"LD_PRELOAD": "/home/william/Workspaces/GameHarness/build/time_control.so",
                       "TIME_CHANNEL": str(channel)}
        proc = subprocess.Popen(["./a.out"], \
                                env = environment,
                                stdout = subprocess.PIPE)
        time.sleep(1)
        proc.kill()
        out = proc.stdout.read()

        output = out.decode("UTF-8")
        print(output)
        ticks = output.count("tick")
        assert speedup - 1 <= ticks <= speedup + 1, f"Set speed-up to {speedup} but only hit {ticks} ticks."
    print("Time writer tests passed!")
