import time

# Prints the fps of the calling code.
# - Disable by setting 'print_interval' to None.
# - If 'throttle_fps' is not None, the helper will throttle the calling code to
#   the given fps.
class Helper():
    def __init__(self, print_interval = 1, throttle_fps = None):
        self.interval = print_interval
        self.throttle_fps = throttle_fps
        self.tick_start = time.time()
        self.ticks_in_interval = 0

    def _CheckNewInterval(self, cur):
        if cur % self.interval <= self.tick_start % self.interval:
            print("FPS:", self.ticks_in_interval)
            self.ticks_in_interval = 0

    def __call__(self):
        if self.interval is None:
            return

        cur = time.time()
        self._CheckNewInterval(cur)

        if self.throttle_fps is not None:
            tick_duration = 1 / self.throttle_fps
            tick_end = time.time()
            elapsed = tick_end - self.tick_start
            sleep_length = tick_duration - elapsed

            if sleep_length > 0:
                time.sleep(sleep_length)

        cur = time.time()
        if self.ticks_in_interval > 0:
            self._CheckNewInterval(cur)

        self.tick_start = cur
        self.ticks_in_interval += 1
