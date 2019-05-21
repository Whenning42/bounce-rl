from PIL import Image
from datetime import datetime
import time
import numpy as np
import os
import random

# Setup an advesarial curiosity model
#   The agent tries to maximize model uncertainty
#   The model tries to predict the next input frame

SAVE_DIR = "memories/"

# It's worth noting that after decompression, the training bitmaps will be fairly large
class Model(object):
    def __init__(self):
        # Name the model after it's initialization time
        self.save_path = SAVE_DIR + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + "/"
        os.mkdir(self.save_path)
        self.last_action = np.zeros(84)
        self.startup = 0
        self.current_observation = 0

    # State is a bitmap, action is a keymap, and reward is a float
    # The format of these files could probably be improved but this is alright for now
    def save_state(self, state, action, reward):
        observation_path = self.save_path + str(self.current_observation)
        timestamp = datetime.now().timestamp()

        image = Image.fromarray(state)
        image.save(observation_path + ".png")

        action_file = open(observation_path + ".keymap", "w")
        action.astype('uint8').tofile(action_file)

        timestamp_file = open(observation_path + ".timestamp", "w")
        timestamp_file.write(str(timestamp))

        reward_file = open(observation_path + ".reward", "w")
        reward_file.write(str(reward))

        self.current_observation += 1

    # State is a bitmap, action is a keymap, and reward is a float
    # The format of these files could probably be improved but this is alright for now
    def load_state(self, observation_path):
        image = Image.load(observation_path + ".png")
        state = np.array(image)

        action_file = open(observation_path + ".keymap", "r")
        action = np.fromfile(action_file, dtype='uint8')

        reward_file = open(observation_path + ".reward", "r")
        reward = float(timestamp_file.readline().strip())

        timestamp_file = open(observation_path + ".timestamp", "r")
        timestamp = float(timestamp_file.readline().strip())

        return state, action, reward, timestamp

    def update(self, state, reward):
        action_keymap = np.zeros(84)

        if self.startup < 20 * 15:
            if int(time.time() * 10) % 2 == 0:
                action_keymap[57] = 1
            else:
                action_keymap[57] = 0
            self.startup += 1

        elif 0 == 0:
            action_keymap[random.randint(0, 83)] = 1
        else:
            action_keymap = self.last_action

        self.save_state(state, action_keymap, reward)

        self.last_action = action_keymap
        return action_keymap

