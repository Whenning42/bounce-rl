# Implements a Console class that launches a command line prompt in a new XTerm window and
# reads input from the prompt in a non-blocking manner.
#
# Example Usage:
#   import time
#   c = Console()
#   while c.is_open:
#       time.sleep(.1)
#       for command in c.CommandQueue():
#           print(command)

import random
import os.path
import os
import subprocess
import atexit

pipe_paths = []

@atexit.register
def cleanup_pipes():
    for path in pipe_paths:
        os.remove(path)

class Console():
    def __init__(self):
        self.is_open = True
        PIPE_NAME = "command_pipe"

        fifo_path = ""
        while True:
            fifo_id = hex(random.randint(0, 2**16-1))[2:]
            fifo_path = "/tmp/" + PIPE_NAME + fifo_id
            if not os.path.exists(fifo_path):
                break

        os.mkfifo(fifo_path)
        pipe_paths.append(fifo_path)
        subprocess.Popen(["xterm", "-hold", "-e", "build/console.bin", fifo_path])
        self.fifo = os.open(fifo_path, os.O_RDONLY | os.O_NONBLOCK)

    def CommandQueue(self):
        try:
            buffer = os.read(self.fifo, 2048)
            if len(buffer) == 0:
                self.is_open = False
                return []
            else:
                return buffer.decode('utf-8').strip().split('\n')
        except BlockingIOError as err:
            return []
