from harness import *
import run_configs

harness = Harness(run_configs.LoadConfig("Minecraft"))
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
