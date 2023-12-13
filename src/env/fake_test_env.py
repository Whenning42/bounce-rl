import gym


# Uses the old style gym API.
class FakeTestEnv(gym.Env):
    def __init__(
        self,
        done_after: int = 5,
        observation_space: gym.spaces.Space = None,
        action_space: gym.spaces.Space = None,
    ):
        self.i = 0
        self.done_after = done_after
        self.closed = False

        if observation_space is None:
            observation_space = gym.spaces.Discrete(2)
        self.observation_space = observation_space

        if action_space is None:
            action_space = gym.spaces.Discrete(3)
        self.action_space = action_space

    def step(self, action):
        if self.closed:
            return None, None, None, None

        obs = self.i
        rew = action
        done = False
        if self.i >= self.done_after - 1:
            done = True
        info = {}

        self.i += 1
        return obs, rew, done, info

    def reset(self, seed=None):
        self.i = 0
        return self.i

    def close(self):
        self.closed = True
