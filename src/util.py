import numpy as np
from typing import Any

class LinearInterpolator:
    def __init__(self, x_0, x_1, y_0, y_1, extrapolate=False):
        self.x_0 = x_0
        self.x_1 = x_1
        self.y_0 = y_0
        self.y_1 = y_1
        self.extrapolate = extrapolate

    def get_value(self, x):
        x_p = (x - self.x_0) / (self.x_1 - self.x_0)
        if not self.extrapolate:
            x_p = np.clip(x_p, 0, 1)
        return self.y_0 + x_p * (self.y_1 - self.y_0)

class GrowingCircularFIFOArray:
    """A circular array that can grow upon looping. The caller requests the desired
    array size with each push. The requested sizes must monotonically increase."""
    def __init__(self, max_size: int, dtype: type = np.float32):
        self.i = 0
        self.max_requested_size = -float('inf')

        self.mask = np.full((max_size,), False)
        self.array = np.empty(max_size)

    def __len__() -> int:
        return np.sum(self.mask) 

    def get_array(self) -> np.ndarray:
        return self.array[self.mask]

    def push(self, x: Any, requested_size: int) -> None:
        assert requested_size <= self.array.shape[0]
        assert requested_size >= self.max_requested_size

        self.i = self.i % requested_size
        self.array[self.i] = x
        self.mask[self.i] = True
        self.i += 1
        self.max_requested_size = requested_size
