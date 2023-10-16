# TODO: Add tests once we've got containerization set up. Use fixed seed + golden image and
# L1 distance to set up a pass / fail threshold.
#
# FIXME: Noita's window doesn't always recieve focus, even when moving the
# mouse over if with fake input. Maybe is related to killing the old noita
# window. An x11 session per episdode would solve the issue.


import os
import time
from enum import Enum
from typing import Any, Iterable, Optional, Callable
from dataclasses import dataclass

import gym
import numpy as np
import pathlib
import PIL.Image

import configs.app_configs as app_configs
import keyboard
import rewards.noita_info
import rewards.noita_reward
import src.time_writer
from src.util import GrowingCircularFIFOArray, LinearInterpolator
from harness import Harness

@dataclass
class StepVal:
    pixels: np.ndarray
    reward: float
    terminated: bool
    truncated: bool
    info: dict
    ep_step: int
    env_step: int

class NoitaState(Enum):
    UNKNOWN = 0
    RUNNING = 1
    GAME_OVER = 2

def is_overworld(info: dict) -> bool:
    if int(info['y']) < -80:
        return True
    return False

class TerminateOnOverworld:
    """Terminate the episode if the player is in the overworld."""
    def __call__(self, step: StepVal) -> StepVal:
        if is_overworld(step.info):
            step.terminated = True
        return step

class TerminateOnSparseReward:
    """Terminate the episode if the reward is zero for too many steps."""
    def __init__(self, history_len: Optional[LinearInterpolator] = None, max_size: Optional[int] = None):
        self.termination_penalty = 10
        if max_size is None:
            max_size = 5*60*4
        self.reward_history = GrowingCircularFIFOArray(max_size=max_size)
        if history_len is None:
            history_len = LinearInterpolator(x_0=0, x_1=1000000, y_0=1.5*60*4, y_1=5*60*4, extrapolate=False)
        self.history_len = history_len

        # Push a non-zero reward to prevent early termination.
        self.reward_history.push(1, 1)

    def __call__(self, step: StepVal) -> StepVal:
        self.reward_history.push(step.reward, int(self.history_len.get_value(step.ep_step)))
        reward_history = self.reward_history.get_array()
        if np.sum(reward_history != 0) == 0:
            step.reward -= self.termination_penalty
            step.terminated = True
            print(f"Terminated an episode due to sparse reward at step {step.ep_step}.")
        return step


class NoitaEnv(gym.core.Env):
    def __init__(
        self,
        out_dir: Optional[str] = None,
        # We're not yet launching noita with time control LD_PRELOAD. Once we do,
        # we can set run_rate and pause_rate to 4 and 0.25 respectively.
        run_rate: float = 1,
        pause_rate: float = 1,
        env_conf: Optional[dict] = None,
        # Defaults to TerminateOnOverworld and TerminateOnSparseReward
        step_wrappers: list[Optional[Callable[StepVal, StepVal]]] = None,
    ):
        self.out_dir = out_dir
        self.run_rate = run_rate
        self.pause_rate = pause_rate
        if env_conf is None:
            env_conf = {}
        self.env_conf = env_conf
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
        self.reward_callback = rewards.noita_reward.NoitaReward()

        if step_wrappers is None:
            step_wrappers = [TerminateOnOverworld(), TerminateOnSparseReward()]
        self.step_wrappers = step_wrappers

        # TODO: Add mouse velocity as a feature.
        # TODO: Add inventory (I) as an input.
        self.input_space = [
            ("W", "S"),
            ("A", "D"),
            ("F",),
            ("E",),
            ("1", "2", "3", "4"),
            ("5", "6", "7", "8"),
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
            low=0, high=255, shape=(self.run_config["y_res"], self.run_config["x_res"], 3), dtype=np.uint8
        )

        self.ep_step = 0
        self.ep_num = 0
        self.env_step = 0

        self._reset_env(skip_startup=True)

    def _reset_env(self, skip_startup: bool=False):
        self.ep_step = 0
        self.ep_num += 1
        self.image_dir = f"{self.out_dir}/screenshots/ep_{self.ep_num}"
        self.step_dir = f"{self.out_dir}/steps/ep_{self.ep_num}"
        pathlib.Path(self.image_dir).mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.step_dir).mkdir(parents=True, exist_ok=True)

        if hasattr(self, "harness"):
            # Release keys before we delete the old harness instance.
            # Important because the new harness won't know which keys
            # were held.
            self.harness.keyboards[0].set_held_keys(set())
            time.sleep(.1)
            self.harness.kill_subprocesses()
            time.sleep(1)
            os.system('killall noita.exe')
            time.sleep(1)
        self.harness = Harness(self.app_config, self.run_config)
        self.state = NoitaState.UNKNOWN
        self._wait_for_harness_init()
        self._env_init(skip_startup=skip_startup)

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
        time.sleep(.5)
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
        run_sequence = ((7.2, ("D",)), (1.0, ("W", "D")), (5, ("D",)))
        for t, keys in run_sequence + ((0, ()),):
            self.harness.keyboards[0].set_held_keys(keys)
            time.sleep(t)

    def _env_init(self, skip_startup: bool):
        print("Running NoitaEnv init!")
        if not skip_startup:
            self._run_init_sequence()
        self.state = NoitaState.RUNNING

    # Stable baselines3 requires a seed method.
    def seed(self, seed):
        pass

    # SB3 expects `done` instead of `terminated` and `truncated`.
    # def step(self, action: tuple[Iterable, Iterable]) -> tuple[np.ndarray, float, bool, bool, dict]:
    def step(self, action: tuple[Iterable, Iterable]) -> tuple[np.ndarray, float, bool, dict]:
        self.ep_step += 1
        self.env_step += 1

        # Convert actions to device inputs
        # My SB3 implementation flattens the space, here we split it back out again.
        if len(action) == 9:
            action = action[0:7], action[7:9]
        discrete_action, continuous_action = action
        discrete_action = [int(x) for x in discrete_action]
        
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

        # Compute step values
        info = self.info_callback.on_tick()
        reward = self.reward_callback.update(info)
        terminated = not info["is_alive"]
        truncated = False
        step_val = StepVal(pixels, reward, terminated, truncated, info, self.ep_step, self.env_step)

        # Apply any step wrappers
        for wrapper in self.step_wrappers:
            step_val = wrapper(step_val)

        # Save screenshots (400kBps)
        im = PIL.Image.fromarray(step_val.pixels)
        im.save(f"{self.image_dir}/step_{self.ep_step}.png")

        # Save step values minus pixels
        save_val = StepVal(None, step_val.reward, step_val.terminated, step_val.truncated, step_val.info, step_val.ep_step, step_val.env_step)
        np.save(f"{self.step_dir}/step_{self.ep_step}.npy", save_val)

        # return pixels, reward, terminated, truncated, info
        return step_val.pixels, step_val.reward, step_val.terminated or step_val.truncated, step_val.info

    # SB3 doesn't handle info returned in reset method.
    # def reset(self, *, seed: Any = None, options: Any = None) -> tuple[gym.core.ObsType, dict]:
    def reset(self, *, seed: Any = None, options: Any = None) -> gym.core.ObsType:
        """Seed isn't yet implemented. Options are ignored."""
        print("Called reset")
        self._reset_env()
        pixels = self.harness.get_screen()
        info = self.info_callback.on_tick()
        # return pixels, info
        return pixels

    def run_info(self):
        return {'episode_step': self.ep_step,
                'environment_step': self.env_step}
