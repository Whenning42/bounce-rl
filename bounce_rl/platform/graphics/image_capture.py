import numpy as np

# TODO: Add vkvfb python bindings.
import Vkvfb

from bounce_rl.platform import WindowConnection


class ImageCapture:
    def __init__(self, window: WindowConnection):
        self._window = window
        self._vkvfb = Vkvfb(window)

    def get_image(self) -> np.ndarray:
        b, w, h = self._vkvfb.read()
        arr = np.frombuffer(b).reshape(h, w, 4)
        assert not arr.flags["OWNDATA"]
        return arr
