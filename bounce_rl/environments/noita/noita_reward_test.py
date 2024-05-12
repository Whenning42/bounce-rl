import unittest

from bounce_rl.environments.noita import noita_reward


class TestArtOfRallyReward(unittest.TestCase):
    def _valid_info(self):
        """An arbitrary valid info dict."""
        return {"hp": 100, "max_hp": 100, "gold": 0, "x": 0, "y": 0, "polymorphed": 0}

    def test_lost_hp(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["hp"] = 100
        new_info = self._valid_info()
        new_info["hp"] = 90

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, -10 * reward_class.LOST_HP_K)

    def test_gained_hp(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["hp"] = 100
        new_info = self._valid_info()
        new_info["hp"] = 110

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, 10 * reward_class.GAINED_HP_K)

    def test_lost_max_hp(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["max_hp"] = 100
        new_info = self._valid_info()
        new_info["max_hp"] = 90

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, -10 * reward_class.DMAX_HP_K)

    def test_gained_max_hp(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["max_hp"] = 100
        new_info = self._valid_info()
        new_info["max_hp"] = 110

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, 10 * reward_class.DMAX_HP_K)

    def test_spent_gold(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["gold"] = 100
        new_info = self._valid_info()
        new_info["gold"] = 90

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, 10 * reward_class.SPENT_GOLD_k)

    def test_gained_gold(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["gold"] = 100
        new_info = self._valid_info()
        new_info["gold"] = 110

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, 10 * reward_class.GAINED_GOLD_K)

    def test_entering_new_block(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["x"] = 0
        initial_info["y"] = 0
        new_info = self._valid_info()
        new_info["x"] = 5000
        new_info["y"] = 5000

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, reward_class.BLOCK_K)

    def test_polymorphed(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["polymorphed"] = 0
        new_info = self._valid_info()
        new_info["polymorphed"] = 1

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, -reward_class.POLYMORPHED_K)


if __name__ == "__main__":
    unittest.main()
