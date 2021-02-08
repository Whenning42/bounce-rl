from harness import *

harness = Harness()
model = Model()

from PIL import Image
import numpy as np

while harness.tick():
    bitmap = harness.get_screen()
    if bitmap is not None:
        keymap = model.update(bitmap)
        harness.perform_actions(keymap)
    else:
        print("No bitmap")
