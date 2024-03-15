import gym
import numpy as np

class FakeGym(gym.Env):
    def __init__(self, is_discrete = False):
        if not is_discrete:
            self.action_space = gym.spaces.Box(low = np.array((-1, -1)), high = np.array((1, 1)))
        obs_shape = (480, 640, 1)
        self.observation_space = gym.spaces.Box(low = np.zeros(obs_shape),
                                                high = np.ones(obs_shape) * 255,
                                                dtype = np.uint8)
        self.i = 0

    def step(self, action):
        obs = self.observation_space.sample()
        reward = np.mean(obs)
        self.i += 1
        done = self.i % 3 == 0
        info = {}
        # My environment's API:
        return obs, reward, done, info

        # Real Gym API:
        # return obs, reward, terminated, truncated, info

    def reset(self):
        obs = self.observation_space.sample()
        # My environment's API:
        return obs

        # Real Gym API:
        # return obs, reward, terminated, truncated, info

    def render(self):
        pass

    def close(self):
        pass
