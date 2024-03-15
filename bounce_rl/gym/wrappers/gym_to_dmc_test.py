import gym_to_dmc
import fake_gym

from absl.testing import absltest
from dm_env import test_utils

class GymToDmcTest(test_utils.EnvironmentTestMixin, absltest.TestCase):
    def make_object_under_test(self):
        return gym_to_dmc.GymToDmc(fake_gym.FakeGym())

if __name__ == "__main__":
    absltest.main()
