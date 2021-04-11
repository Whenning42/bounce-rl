from harness import *
import run_configs
import model
import ros

harness = Harness(run_configs.LoadConfig("Minecraft"))

agent = model.ImageRecordAgent()
# agent = ros.ROSCameraNode(960, 540)

from PIL import Image
import numpy as np

while harness.tick():
    bitmap = harness.get_screen()
    if bitmap is not None:
        keymap = agent.update(bitmap)
        harness.perform_actions(keymap)
    else:
        print("No bitmap")
