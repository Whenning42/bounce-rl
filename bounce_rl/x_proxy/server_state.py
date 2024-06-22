# The ServerState class holds X server state that the proxy manages.
# An example is cursor position management in the proxy via SendEvent;
# in this case, the proxy needs to know store the latest SendEvent cursor
# position, so as to be able to reply with this position to any Query Pointer requests.

import threading


class ServerState:
    def __init__(self):
        self.pointer_state_init = False
        self.pointer_window = 0
        self.pointer_root_x = 0
        self.pointer_root_y = 0

        self._lock = threading.Lock()

    def lock(self):
        self._lock.acquire()

    def unlock(self):
        self._lock.release()
