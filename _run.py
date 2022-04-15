from harness import *
import app_configs
import model
import rewards.art_of_rally
import callbacks.callbacks as callbacks

START_FRAME = 0
OUT_DIR = "out/"

art_of_rally_reward_callback = \
        rewards.art_of_rally.ArtOfRallyReward(plot_output = True, out_dir = OUT_DIR, start_frame = START_FRAME)
screenshot_callback = callbacks.ScreenshotCallback(out_dir = OUT_DIR, start_frame = START_FRAME)
run_config = {
    "title": "Art of Rally reward eval",
    "app": "Art of Rally",
    "max_tick_rate": 5,
#    "on_tick": (art_of_rally_reward_callback, screenshot_callback),
    "on_tick": (screenshot_callback,),
    "x_res": 1920,
    "y_res": 1080,
    "scale": .5,
}
app_config = app_configs.LoadAppConfig(run_config["app"])
harness = Harness(app_config, run_config)
art_of_rally_reward_callback.attach_to_harness(harness)
screenshot_callback.attach_to_harness(harness)

from PIL import Image
import numpy as np

while harness.tick():
    # We don't have an agent
    continue

    # This code would run an agent if we had one.
    # bitmap = harness.get_screen()
    # if bitmap is not None:
    #     keymap = agent.update(bitmap)
    #     harness.perform_actions(keymap)
    # else:
    #     print("No bitmap")
