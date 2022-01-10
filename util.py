import json
import numpy as np

def LoadJSON(filename):
    with open(filename) as f:
        loaded = json.load(f)
    return loaded

import time
from contextlib import contextmanager
@contextmanager
def TimeBlock(name):
    start = time.perf_counter()
    try:
        yield
    finally:
        interval = time.perf_counter() - start
        print(f"Block {name} took {round(interval * 1000)} milliseconds")

def npBGRAtoRGB(array):
    return np.flip(array[:, :, :3], axis = 2).copy()
