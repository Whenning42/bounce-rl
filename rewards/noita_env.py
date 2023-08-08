# TODO: Add tests once we've got containerization set up. Use fixed seed + golden image and
# L1 distance to set up a pass / fail threshold.

import logging
import time
from enum import Enum
from typing import Any, Iterable, Optional

import gym
import numpy as np

import configs.app_configs as app_configs
import keyboard
import rewards.noita_info
import src.time_writer
from harness import Harness

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


class NoitaState(Enum):
    UNKNOWN = 0
    RUNNING = 1
    GAME_OVER = 2


class NoitaEnv(gym.core.Env):
    def __init__(
        self,
        out_dir: Optional[str] = None,
        # We're not yet launching noita with time control LD_PRELOAD. Once we do,
        # we can set run_rate and pause_rate to 4 and 0.25 respectively.
        run_rate: float = 1,
        pause_rate: float = 1,
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
        self.run_config: dict[str, Any] = run_config
        self.app_config = app_configs.LoadAppConfig(run_config["app"])
        self.info_callback = rewards.noita_info.NoitaInfo()

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
        self.action_space = gym.spaces.Tuple(
            (
                gym.spaces.MultiDiscrete(discrete_lens),
                gym.spaces.Box(low=-1, high=1, shape=(2,)),
            )
        )
        self.observation_space = gym.spaces.Box(
            low=0, high=255, shape=(480, 640, 3), dtype=np.uint8
        )
        self.harness = None
        self._reset_env()

    def _reset_env(self):
        if self.harness is not None:
            self.harness.kill_subprocesses()
        self.harness = Harness(self.app_config, self.run_config)
        self.state = NoitaState.UNKNOWN
        self._wait_for_harness_init()
        self._env_init()

    def _wait_for_harness_init(self):
        while not self.harness.ready:
            self.harness.tick()
            time.sleep(0.5)
            print("Waiting for harness")
        print("Finished harness init!")

    def _select_mode_macro(self) -> list[str]:
        return [
            "Down",
            "Down",
            "Down",
            "Down",
            "Return",
        ]

    def _run_init_sequence(self):
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
            *self._select_mode_macro(),
        )
        self.harness.keyboards[0].move_mouse(10, 10)
        self.harness.keyboards[0].key_sequence(menu_keys)

        # Fly into the mines
        time.sleep(10)
        run_sequence = ((7, ("D",)), (0.8, ("W", "D")), (7, ("D",)))
        for t, keys in run_sequence + ((0, ()),):
            self.harness.keyboards[0].set_held_keys(keys)
            time.sleep(t)

    def _env_init(self):
        print("Running NoitaEnv init!")
        self._run_init_sequence()
        self.state = NoitaState.RUNNING

    def step(self, action: tuple[Iterable, Iterable]) -> tuple[np.ndarray, float, bool, bool, dict]:
        # Convert actions to device inputs
        discrete_action, continuous_action = action
        held_mouse_buttons = set()
        held_keys = set()
        for i, s in zip(discrete_action, self.input_space):
            if s[i] is not None and not isinstance(s[i], keyboard.MouseButton):
                held_keys.add(s[i])
            if s[i] is not None and isinstance(s[i], keyboard.MouseButton):
                held_mouse_buttons.add(s[i])

        # Apply inputs
        self.harness.keyboards[0].set_held_keys(held_keys)
        self.harness.keyboards[0].set_held_mouse_buttons(held_mouse_buttons)
        continuous_action = [(c + 1) / 2 for c in continuous_action]
        mouse_pos = (
            continuous_action[0] * self.run_config["x_res"],
            continuous_action[1] * self.run_config["y_res"],
        )
        self.harness.keyboards[0].move_mouse(*mouse_pos)

        # Step the harness
        # TODO: Move time control into harness
        self.harness.tick()
        src.time_writer.SetSpeedup(self.run_config["run_rate"])
        time.sleep(self.run_config["step_duration"] / self.run_config["run_rate"])
        src.time_writer.SetSpeedup(self.run_config["pause_rate"])
        pixels = self.harness.get_screen()

        # Return env outputs
        info = self.info_callback.on_tick()
        reward = 0  # TODO: Design reward functions.
        terminated = not info["is_alive"]
        truncated = False
        return pixels, reward, terminated, truncated, info

    # Optionally, could restart harness on reset.
    def reset(self, *, seed: Any = None, options: Any = None) -> tuple[gym.core.ObsType, dict]:
        """Seed isn't yet implemented. Options are ignored."""
        print("Called reset")
        if self.state == NoitaState.GAME_OVER:
            seq = [
                "Escape",
                "Down",
                "Return",
                *self._select_mode_macro(),
            ]
            self.harness.keyboards[0].key_sequence(seq)
        elif self.state == NoitaState.RUNNING:
            seq = [
                "Escape",
                "Down",
                "Down",
                "Return",
                *self._select_mode_macro(),
                "Left",
                "Return",
            ]
            self.harness.keyboards[0].key_sequence(seq)
        else:
            logging.warning("Called reset prior to game start. Blocking until env init.")
            while self.state not in (NoitaState.RUNNING, NoitaState.GAME_OVER):
                time.sleep(5)
                logging.warning("NoitaEnv reset blocking...")

        pixels = self.harness.get_screen()
        info = self.info_callback.on_tick()
        return pixels, info
