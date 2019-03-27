from PIL import Image
from datetime import datetime
import time
import numpy as np
import os

# Setup an advesarial curiosity model
#   The agent tries to maximize model uncertainty
#   The model tries to predict the next input frame

# It's worth noting that after decompression, the training bitmaps will be fairly large
class Model(object):
    def __init__(self):
        # Name the model after it's initialization time
        self.name = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S:%f')
        os.mkdir("memories/" + self.name)
        self.last_action = np.zeros(84)

    def save_state(self, bitmap, keymap):
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S:%f')

        # Could hurt performance badly
        bitmap = bitmap[:, :, [2, 1, 0]]
        im = Image.fromarray(bitmap)
        im.save("memories/" + self.name + "/" + timestamp + ".png")

        f = open("memories/" + self.name + "/" + timestamp + ".keymap", "w")
        keymap.astype('uint8').tofile(f)

    def get_action(self, bitmap):
        action_keymap = np.zeros(84)

        if random.randint(0, 19) == 0:
            action_keymap[random.randint(0, 83)] = 1
        else:
            action_keymap = self.last_action
        self.save_state(bitmap, action_keymap)

        self.last_action = action_keymap
        return action_keymap

