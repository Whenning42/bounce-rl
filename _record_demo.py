import rewards.env_rally
import random
import evdev
from src.keyboard.controller import Controller

# Build with:
# $ cd src/keyboard
# $ make
# $ cp src/keyboard/UserKeyboard/* ./
# Note: Virtualenv might get the compiled so name's python version wrong.
# If so, this needs to be manually fixed.
import UserKeyboard

discrete = True

# Create environment
env = rewards.env_rally.ArtOfRallyEnv(out_dir = "analog_demo_0", run_rate = 1.0, pause_rate = .1)

p_conf = {"steps_between": int(2.5 * 8),
          "max_duration": 8,
          "space": env.action_space}

class Perturb:
    def __init__(self, conf):
        self.t = 0
        self.conf = conf
        self.cycle_len = self.conf["steps_between"]
        self.duration = -1
        self.action = None

    def step(self):
        self.t += 1
        cycle_t = self.t % self.cycle_len
        if cycle_t == 0:
            random.seed(cycle_i)
            self.duration = random.randint(0, self.conf["max_duration"])
            self.action = env.action_space.sample()
            return self.action
        elif cycle_t < self.duration:
            return self.action
        else:
            return None


def ApplyAction(controller, action): 
    controller.inject(3, evdev.ecodes.ABS_X, action[0]) 
    controller.inject(3, evdev.ecodes.ABS_RX action[1]) 
    controller.inject(3, evdev.ecodes.ABS_RY, action[2]) 

p = Perturb(p_conf)
cont = Controller()
cont.register_callback(env.on_input)
kb = UserKeyboard.UserKeyboard()
env.reset()
took_action = False
while True:
    # U,   D,   L,   R
    # 111, 116, 113, 114
    action = p.step()
    perturbed = action is not None
    if discrete:
        if perturbed:
            kb.disable()
            to_log = None
            took_action = True
        else:
            if took_action:
                env.harness.keyboards[0].set_held_keys(set())
            kb.enable()
            to_log = [0, 0]
            state = kb.key_state()
            if state[111] and not state[116]:
                to_log[0] = 1
            elif state[116] and not state[111]:
                to_log[0] = 2
            if state[113] and not state[114]:
                to_log[1] = 1
            elif state[114] and not state[113]:
                to_log[1] = 2
            took_action = False
        _, _, done, _ = env.step(action, logged_action=to_log, perturbed=perturbed)
    else:
        if perturbed:
            ApplyAction(cont, action)
            controller.lock_user()
        else:
            controller.unlock_user()
        _, _, done, _ = env.step(perturbed=pertubed)

    if done:
        kb.disable()
        env.reset()
        kb.enable()
