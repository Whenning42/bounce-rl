import unittest

import numpy as np

from bounce_rl.environments.noita.noita_env import StepVal, TerminateOnSparseReward
from bounce_rl.utilities.util import LinearInterpolator


def other_args():
    return {'pixels': np.zeros((16, 16, 3), dtype=np.uint8),
            'info': {},
            'terminated': False,
            'truncated': False,
            'env_step': 0}

class TestTerminateOnSparseReward(unittest.TestCase):
    def test_not_terminated_at_start(self):
        terminator = TerminateOnSparseReward(LinearInterpolator(x_0=0, x_1=10000, y_0=3, y_1=3))
        self.assertFalse(terminator(StepVal(reward=0, ep_step=0, **other_args())).terminated)
        self.assertFalse(terminator(StepVal(reward=0, ep_step=1, **other_args())).terminated)
        self.assertTrue(terminator(StepVal(reward=0, ep_step=2, **other_args())).terminated)

    def test_sparse_len_is_respected(self):
        terminator = TerminateOnSparseReward(LinearInterpolator(x_0=0, x_1=10000, y_0=10, y_1=20))
        for i in range(9):
            step = terminator(StepVal(reward=0, ep_step=i, **other_args()))
            self.assertFalse(step.terminated)
        step = terminator(StepVal(reward=0, ep_step=i, **other_args()))
        self.assertTrue(step.terminated)

        terminator = TerminateOnSparseReward(LinearInterpolator(x_0=0, x_1=10000, y_0=10, y_1=20))
        for i in range(9900):
            step = terminator(StepVal(reward=1, ep_step=i, **other_args()))
            self.assertFalse(step.terminated)
        for i in range(9900, 9918):
            step = terminator(StepVal(reward=0, ep_step=i, **other_args()))
            self.assertFalse(step.terminated)
        step = terminator(StepVal(reward=0, ep_step=i, **other_args()))
        self.assertTrue(step.terminated)

    def test_termination_penalizes_reward(self):
        terminator = TerminateOnSparseReward(LinearInterpolator(x_0=0, x_1=10, y_0=10, y_1=10))
        for i in range(20):
            step = terminator(StepVal(reward=0, ep_step=i, **other_args()))
        self.assertTrue(step.terminated)
        self.assertEqual(step.reward, -10)

if __name__ == "__main__":
    unittest.main()