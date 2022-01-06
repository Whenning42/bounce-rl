# An class for predicting the current reward for an Art of Rally game running in the Harness.

import harness
import pathlib
from PIL import Image

class ScreenshotCallback():
    def __init__(self, out_dir = None, start_frame = 0):
        self.out_dir = out_dir
        pathlib.Path(self.out_dir).mkdir(parents = True, exist_ok = True)

        # The capture methods are initialized in set_harness().
        self.capture_frame = None
        self.frame = start_frame

    # Initializes the capture ROI methods using capture instances created in the harness.
    def attach_to_harness(self, harness):
        self.harness = harness
        self.capture_frame = harness.add_capture((0, 0, 1920, 1080))

    def on_tick(self):
        captured_frame = self.capture_frame()

        filename = f"{self.frame:04d}.png"
        im = Image.fromarray(captured_frame)
        im.save(self.out_dir + filename)

        self.frame += 1
