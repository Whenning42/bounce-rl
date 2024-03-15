import unittest

import gym.spaces

from src.env.fake_test_env import FakeTestEnv
from src.env.subproc_env import SubprocEnv


class TestSubprocEnv(unittest.TestCase):
    def test_observation_space(self):
        observation_space = gym.spaces.Discrete(5)
        child_env = FakeTestEnv(observation_space=observation_space)
        env = SubprocEnv(lambda: child_env)
        self.assertEqual(env.observation_space, observation_space)

    def test_action_space(self):
        action_space = gym.spaces.Discrete(7)
        child_env = FakeTestEnv(action_space=action_space)
        env = SubprocEnv(lambda: child_env)
        self.assertEqual(env.action_space, action_space)

    def test_step(self):
        env = SubprocEnv(lambda: FakeTestEnv(done_after=2))

        action = 3
        obs, rew, done, info = env.step(action)
        self.assertEqual(obs, 0)
        self.assertEqual(rew, action)
        self.assertFalse(done)
        self.assertEqual(info, {})

        action = 2
        obs, rew, done, info = env.step(action)
        self.assertEqual(obs, 1)
        self.assertEqual(rew, action)
        self.assertTrue(done)
        self.assertEqual(info, {})

        # Verify that the SubprocEnv isn't resetting the child env itself.
        obs, rew, done, info = env.step(action)
        self.assertEqual(obs, 2)
        self.assertTrue(done)

    def test_reset(self):
        env = SubprocEnv(lambda: FakeTestEnv(done_after=10))
        obs, rew, done, info = env.step(0)
        self.assertEqual(obs, 0)

        obs = env.reset()
        self.assertEqual(obs, 0)

        _ = env.step(3)
        obs, rew, done, info = env.step(2)
        self.assertEqual(obs, 1)

    def test_close(self):
        # Since close happens out of process, it's a little messy to test.
        # We just verify that it can be called successfully.
        child_env = FakeTestEnv()
        env = SubprocEnv(lambda: child_env)
        env.close()


if __name__ == "__main__":
    unittest.main()
