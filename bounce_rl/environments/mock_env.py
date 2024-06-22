# A mock gym environment for integration testing.

import os
import time
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Tuple

import configs.app_configs as app_configs
import gym
import keyboard
import numpy as np
import rewards.noita_info
import rewards.noita_reward
import src.time_writer
import torch
from harness import Harness


class MockEnv(gym.core.Env):
    def __init__(
        self,
        out_dir: Optional[str] = None,
        # We're not yet launching noita with time control LD_PRELOAD. Once we do,
        # we can set run_rate and pause_rate to 4 and 0.25 respectively.
        run_rate: float = 1,
        pause_rate: float = 1,
        env_conf: Optional[dict] = None,
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
        self.run_config: Dict[str, Any] = run_config
        self.app_config = app_configs.LoadAppConfig(run_config["app"])

        self.ep_step = 0
        self.env_step = 0

        # Action and observation space copied from Noita env.
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
            low=0,
            high=255,
            shape=(self.run_config["y_res"], self.run_config["x_res"], 3),
            dtype=np.uint8,
        )

    # Stable baselines3 requires a seed method.
    def seed(self, seed):
        pass

    # SB3 expects `done` instead of `terminated` and `truncated`.
    # def step(self, action: Tuple[Iterable, Iterable]) -> Tuple[np.ndarray, float, bool, bool, dict]:
    def step(
        self, action: Tuple[Iterable, Iterable]
    ) -> Tuple[np.ndarray, float, bool, dict]:
        self.ep_step += 1
        self.env_step += 1

        pixels = torch.zeros(
            (self.run_config["y_res"], self.run_config["x_res"], 3), dtype=torch.uint8
        )
        info = {}
        reward = 0
        terminated = False
        truncated = False
        # return pixels, reward, terminated, truncated, info
        done = terminated
        return pixels, reward, done, info

    # SB3 doesn't handle info returned in reset method.
    # def reset(self, *, seed: Any = None, options: Any = None) -> Tuple[gym.core.ObsType, dict]:
    def reset(self, *, seed: Any = None, options: Any = None) -> gym.core.ObsType:
        """Seed isn't yet implemented. Options are ignored."""
        pixels = torch.zeros(
            (self.run_config["y_res"], self.run_config["x_res"], 3), dtype=torch.uint8
        )
        info = {}
        # return pixels, info
        return pixels
