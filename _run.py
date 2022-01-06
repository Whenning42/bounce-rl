from harness import *
import run_configs
import model
import rewards.art_of_rally
import callbacks.callbacks as callbacks

START_FRAME = 238
OUT_DIR = "out/"

art_of_rally_reward_callback = \
        rewards.art_of_rally.ArtOfRallyReward(plot_output = True, out_dir = OUT_DIR, start_frame = START_FRAME)
run_config = {
    "title": "Art of Rally reward eval",
    "app": "Art of Rally",
    "max_tick_rate": 20,
    "on_tick": (art_of_rally_reward_callback, callbacks.ScreenshotCallback(out_dir = OUT_DIR, start_frame = START_FRAME)),
    "x_res": 1920,
    "y_res": 1080,
}
app_config = run_configs.LoadAppConfig(run_config["app"])
harness = Harness(app_config, run_config)
art_of_rally_reward_callback.attach_to_harness(harness)

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
