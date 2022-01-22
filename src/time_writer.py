import subprocess
import time
import struct
import posix

FIFO = "/tmp/time_control"
f = None

def SetSpeedup(speedup):
    global f
    speedup = float(speedup)
    # Opening the file for reading and writing prevents blocking until a reader opens the file.
    if f is None:
        f = posix.open(FIFO, posix.O_RDWR | posix.O_CREAT)
    posix.ftruncate(f, 0)
    SEEK_SET = 0
    posix.lseek(f, 0, SEEK_SET)
    posix.write(f, struct.pack("f", speedup))

if __name__ == "__main__":
    for speedup in [12, 18]:
        SetSpeedup(speedup)
        environment = {"LD_PRELOAD": "/home/william/Workspaces/GameHarness/build/time_control.so"}
        proc = subprocess.Popen(["./a.out"], \
                                env = environment,
                                stdout = subprocess.PIPE)
        time.sleep(1)
        proc.kill()
        out = proc.stdout.read()

        ticks = out.decode("UTF-8").count("tick")
        assert(speedup - 1 <= ticks <= speedup + 1)
    print("Time writer tests passed!")
