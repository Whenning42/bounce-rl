from typoing import Optional
import time
import gin
import gym
import numpy as np
import configs.app_configs as app_configs
from harness import Harness
import rewards.noita
import keyboard

# Env design:
#   required harness env params:
#    - run rate
#    - pause rate
#
#   optional env params:
#    - logging directory
#
#   env specific params:
#    - gamma, reward model, ...


@gin.configurable
class NoitaEnv(gym.core.Env):
    def __init__(
        self,
        out_dir: Optional[str] = None,
        run_rate: float = 4,
        pause_rate: float = 0.25,
    ):
        self.out_dir = out_dir
        self.run_rate = run_rate
        self.pause_rate = pause_rate

        run_config = {
            "app": "Noita",
            "x_res": 640,
            "y_res": 360,
            "scale": 1,
            "run_rate": run_rate,
            "pause_rate": pause_rate,
            "step_duration": 0.25,
            "pixels_every_n_episodes": 1,
        }
        self.run_config = run_config
        app_config = app_configs.LoadAppConfig(run_config["app"])
        harness = Harness(app_config, run_config)
        self.harness = harness

        noita_reward_callback = rewards.noita.NoitaReward()

        # TODO: Add mouse velocity as a feature.
        # TODO: Add inventory (I) and wand switching (2, 3, 4) as features.
        self.input_space = [
            ("W", "S"),
            ("A", "D"),
            ("F",),
            ("E",),
            ("1",),
            ("5",),
            (keyboard.MouseButton.LEFT, keyboard.MouseButton.RIGHT),
        ]
        self.input_space = [x + (None,) for x in self.input_space]
        discrete_lens = [len(x) for x in self.input_space]
        print(discrete_lens)
        self.action_space = gym.spaces.Tuple(
            (
                gym.spaces.MultiDiscrete(discrete_lens),
                gym.spaces.Box(low=-1, high=1, shape=(2,)),
            )
        )
        self.observation_space = gym.spaces.Box(
            low=0, high=255, shape=(480, 640, 3), dtype=np.uint8
        )

        self._wait_for_harness_init()
        self._env_init()

    def _wait_for_harness_init(self):
        while not self.harness.ready:
            self.harness.tick()
            time.sleep(0.5)
            print("Waiting for harness")
        print("Finished harness init!")

    def _env_init(self):
        print("Running NoitaEnv init!")
        time.sleep(5)
        # Start the game
        menu_keys = (
            # Enter mod settings
            "Down",
            "Down",
            "Down",
            "Return",
            # Hide modding warning (only shows up on a fresh install)
            # "Left",
            # "Return",
            # Enable unsafe
            "Right",
            "Up",
            "Return",
            "Left",
            "Return",
            # Open new game menu
            "Escape",
            "Return",
            # Select rl mod new game
            "Down",
            "Down",
            "Down",
            "Down",
            "Return",
        )
        self.harness.keyboards[0].move_mouse(10, 10)
        self.harness.keyboards[0].key_sequence(menu_keys)

        # Fly into the mines
        time.sleep(10)
        run_sequence = ((7, ("D",)), (0.8, ("W", "D")), (7, ("D",)))
        for t, keys in run_sequence + ((0, ()),):
            self.harness.keyboards[0].set_held_keys(keys)
            time.sleep(t)

    def step(self, action):
        discrete_action, continuous_action = action
        held_mouse_buttons = set()
        held_keys = set()
        for i, s in zip(discrete_action, self.input_space):
            if s[i] is not None and not isinstance(s[i], keyboard.MouseButton):
                held_keys.add(s[i])
            if s[i] is not None and isinstance(s[i], keyboard.MouseButton):
                held_mouse_buttons.add(s[i])

        self.harness.keyboards[0].set_held_keys(held_keys)
        self.harness.keyboards[0].set_held_mouse_buttons(held_mouse_buttons)
        # Remap continuous action from [-1, 1] to [0, 1], then to window coordinates.
        continuous_action = [(c + 1) / 2 for c in continuous_action]
        mouse_pos = (
            continuous_action[0] * self.run_config["x_res"],
            continuous_action[1] * self.run_config["y_res"],
        )
        self.harness.keyboards[0].move_mouse(*mouse_pos)
