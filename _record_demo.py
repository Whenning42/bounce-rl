import rewards.env_rally
import random

# Build with:
# $ cd src/keyboard
# $ make
# $ cp src/keyboard/UserKeyboard/* ./
# Note: Virtualenv might get the compiled so name's python version wrong.
# If so, this needs to be manually fixed.
import UserKeyboard

# Create environment
env = rewards.env_rally.ArtOfRallyEnv(out_dir = "user_demo_0", run_rate = 1, pause_rate = 1)

p_conf = {"steps_between": 8 * 4,
          "duration": 6,
          "space": ((None, "Left", "Right"), (None, "Up", "Down"))}

class Perturb:
    def __init__(self, conf):
        self.t = 0
        self.conf = conf
        self.cycle_len = self.conf["steps_between"] + self.conf["duration"]

    def step(self):
        self.t += 1
        cycle_i = self.t // self.cycle_len
        cycle_t = self.t % self.cycle_len
        if cycle_t < self.conf["duration"]:
            random.seed(cycle_i)
            actions = [random.choice(d) for d in self.conf["space"]]
            actions = [a for a in actions if a is not None]
            return set(actions)
        else:
            return None

import time
p = Perturb(p_conf)
kb = UserKeyboard()
env.reset()
while True:
    action = p.step()
    if action is not None:
        kb.disable()
    else:
        kb.enable()
    env.step(action)
