import unittest

import numpy as np

from src.env.fake_test_env import FakeTestEnv
from src.env.pool_vec_env import PoolVecEnv


class TestPoolVecEnv(unittest.TestCase):
    def test_step(self):
        env = PoolVecEnv([lambda: FakeTestEnv(done_after=2)], n=1, k=1)

        obs, rew, done, info = env.step(np.array([1]))
        self.assertEqual(obs, [0])
        self.assertEqual(rew, [1])
        self.assertEqual(done, [False])
        self.assertEqual(info, [{}])

        obs, rew, done, info = env.step(np.array([2]))
        self.assertEqual(obs, [1])
        self.assertEqual(rew, [2])
        self.assertEqual(done, [True])
        self.assertEqual(info, [{}])

        obs, rew, done, info = env.step(np.array([3]))
        self.assertEqual(obs, [0])
        self.assertEqual(rew, [3])
        self.assertEqual(done, [False])
        self.assertEqual(info, [{}])

    def test_swap_on_done(self):
        c_0 = FakeTestEnv(done_after=2)
        c_1 = FakeTestEnv(done_after=3)
        c_2 = FakeTestEnv(done_after=5)
        env = PoolVecEnv([lambda: c_0, lambda: c_1, lambda: c_2], n=3, k=2)

        obses = []
        rews = []
        dones = []
        for i in range(6):
            obs, rew, done, info = env.step(np.array([0, i]))
            obses.append(obs.tolist())
            dones.append(done.tolist())
            rews.append(rew.tolist())
        self.assertEqual(obses, [[0, 0], [1, 1], [0, 2], [1, 0], [2, 1], [3, 0]])
        self.assertEqual(
            dones,
            [
                [False, False],
                [True, False],
                [False, True],
                [False, False],
                [False, True],
                [False, False],
            ],
        )
        self.assertEqual(rews, [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5]])

    def test_reset(self):
        env = PoolVecEnv([lambda: FakeTestEnv(done_after=2)], n=1, k=1)

        obs, rew, done, info = env.step(np.array([1]))
        self.assertEqual(obs, [0])
        self.assertEqual(rew, [1])
        self.assertEqual(done, [False])
        self.assertEqual(info, [{}])

        obs = env.reset()
        self.assertEqual(obs, [0])

        obs, rew, done, info = env.step(np.array([1]))
        self.assertEqual(obs, [0])
        self.assertEqual(rew, [1])
        self.assertEqual(done, [False])
        self.assertEqual(info, [{}])
