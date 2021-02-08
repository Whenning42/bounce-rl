from harness import *
import Rewards

# model interface
#   get_action(bitmap) returns a keymap to use

harness = Harness()
reward_class = Rewards.autoencoder_loss("pretrained_autoencoder.h5")
harness.setup_reward(reward_class)

# def no_op(a):
#     pass
#
# harness.get_reward = no_op

model = Model()

from PIL import Image
import numpy as np

while harness.tick():
    bitmap = harness.get_screen()
    if bitmap is not None:
        reward = harness.get_reward(bitmap)
        print(reward)
        keymap = model.update(bitmap, reward)
        harness.perform_actions(keymap)
    else:
        print("No bitmap")
