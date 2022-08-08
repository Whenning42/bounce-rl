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
          "space": ((None, "Up", "Down"), (None, "Left", "Right"))}

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
kb = UserKeyboard.UserKeyboard()
env.reset()
while True:
    # U,   D,   L,   R
    # 111, 116, 113, 114
    action = p.step()
    if action is not None:
        kb.disable()
        to_log = None
    else:
        kb.enable()
        to_log = set()
        state = kb.key_state()
        if state[111] and not state[116]:
            to_log.add("Up")
        elif state[116] and not state[111]:
            to_log.add("Down")
        if state[113] and not state[114]:
            to_log.add("Left")
        elif state[114] and not state[113]:
            to_log.add("Right")

    env.step(action)
