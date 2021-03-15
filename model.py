from PIL import Image
from datetime import datetime
import time
import numpy as np
import os
import random

# Setup an advesarial curiosity model
#   The agent tries to maximize model uncertainty
#   The model tries to predict the next input frame

# It's worth noting that after decompression, the training bitmaps will be fairly large
class Model(object):
    def __init__(self):
        # Name the model after it's initialization time
        self.name = datetime.utcnow().strftime('%Y-%m-%d_%H:%M:%S:%f')
        os.mkdir("memories/" + self.name)
        self.last_action = np.zeros(84)
        self.frame = 0

    def _save_state(self, bitmap, keymap):
        filename = str(self.frame)
        save_dir = "memories/" + self.name + "/"

        im = Image.fromarray(bitmap)
        im.save(save_dir + filename + ".png")

        keymap_file = open(save_dir + filename + ".keymap", "w")
        keymap.astype('uint8').tofile(keymap_file)

        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H:%M:%S:%f')
        timestamp_file = open(save_dir + filename + ".timestamp", "w")
        timestamp_file.write(timestamp)

    def update(self, state):
        action_keymap = np.zeros(84)
        self.frame += 1

        # We use a no-op model here to get a user image data.
        self._save_state(state, action_keymap)
        return action_keymap

        # Hardcode pressing enter? to get through menu screen.
        if self.frame < 20 * 15:
            if int(time.time() * 10) % 2 == 0:
                action_keymap[57] = 1
            else:
                action_keymap[57] = 0

        elif 0 == 0:
            action_keymap[random.randint(0, 83)] = 1
        else:
            action_keymap = self.last_action

        self._save_state(state, action_keymap)

        self.last_action = action_keymap
        return action_keymap

