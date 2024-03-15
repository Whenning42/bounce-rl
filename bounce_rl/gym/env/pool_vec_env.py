# Manages n environments of which k are active. The remaining environments are buffers
# swapped into the live set of k on reset to hide slow reset times in the underlying
# environment.
#
# Forked from SB3's SubprocVecEnv.

import concurrent.futures
import queue
import threading
from collections import OrderedDict
from typing import List, Tuple, Union

import gym
import numpy as np
from stable_baselines3.common.vec_env.base_vec_env import VecEnvObs

from bounce_rl.gym.env.subproc_env import SubprocEnv


class PoolVecEnv:
    def __init__(self, env_fns: List[callable], n: int, k: int):
        assert len(env_fns) == n
        assert k <= n

        self.n = n
        self.k = k
        self.num_envs = k

        with concurrent.futures.ThreadPoolExecutor() as executor:
            self.envs = list(executor.map(SubprocEnv, env_fns))
        self.live_envs = self.envs[:k]

        self.ready_queue = queue.Queue()
        for e in self.envs[k:]:
            self._async_reset_env(e)

        self.observation_space = self.envs[0].observation_space
        self.action_space = self.envs[0].action_space

    # TODO: Handle self.observation_space and self.action_space.
    def _async_reset_env(self, env):
        def reset_env(env):
            env.reset()
            if env.env_hasattr("pause"):
                env.env_method("pause")
            self.ready_queue.put(env)

        thread = threading.Thread(target=reset_env, args=(env,), daemon=True)
        thread.start()

    def _reset_live_env(self, i):
        self._async_reset_env(self.live_envs[i])

        self.live_envs[i] = self.ready_queue.get()
        if self.live_envs[i].env_hasattr("resume"):
            self.live_envs[i].env_method("resume")

    def step_async(self, actions: np.ndarray):
        self.actions = actions

    def step_wait(self):
        return self.step(self.actions)

    def step(self, actions: np.ndarray):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(
                executor.map(lambda v: v[0].step(v[1]), zip(self.live_envs, actions))
            )

        # Reset failed environments.
        for i, r in enumerate(results):
            if r is None:
                new_result = None
                while new_result is None:
                    self._reset_live_env(i)
                    new_result = self.live_envs[i].step(actions[i])
                results[i] = new_result

        obs, rews, dones, infos = zip(*results)
        for i, done in enumerate(dones):
            if done:
                self._reset_live_env(i)
        return (
            _flatten_obs(obs, self.observation_space),
            np.stack(rews),
            np.stack(dones),
            list(infos),
        )

    def reset(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            obs = list(executor.map(lambda env: env.reset(), self.live_envs))
        return _flatten_obs(obs, self.observation_space)

    def seed(self, seed=None):
        pass


def _flatten_obs(
    obs: Union[List[VecEnvObs], Tuple[VecEnvObs]], space: gym.spaces.Space
) -> VecEnvObs:
    """
    Flatten observations, depending on the observation space.

    :param obs: observations.
                A list or tuple of observations, one per environment.
                Each environment observation may be a NumPy array, or a dict or tuple
                of numpy arrays.
    :return: flattened observations.
            A flattened NumPy array or an OrderedDict or tuple of flattened numpy
            arrays.
            Each NumPy array has the environment index as its first axis.
    """
    assert isinstance(
        obs, (list, tuple)
    ), "expected list or tuple of observations per environment"
    assert len(obs) > 0, "need observations from at least one environment"

    if isinstance(space, gym.spaces.Dict):
        assert isinstance(
            space.spaces, OrderedDict
        ), "Dict space must have ordered subspaces"
        assert isinstance(
            obs[0], dict
        ), "non-dict observation for environment with Dict observation space"
        return OrderedDict(
            [(k, np.stack([o[k] for o in obs])) for k in space.spaces.keys()]
        )
    elif isinstance(space, gym.spaces.Tuple):
        assert isinstance(
            obs[0], tuple
        ), "non-tuple observation for environment with Tuple observation space"
        obs_len = len(space.spaces)
        return tuple(np.stack([o[i] for o in obs]) for i in range(obs_len))  # type: ignore[index]
    else:
        return np.stack(obs)  # type: ignore[arg-type]
