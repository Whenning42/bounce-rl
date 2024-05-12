import unittest

import noita_reward as noita_reward


class TestArtOfRallyReward(unittest.TestCase):
    def _valid_info(self):
        """An arbitrary valid info dict."""
        return {"hp": 100, "max_hp": 100, "gold": 0, "x": 0, "y": 0}

    def test_lost_hp(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["hp"] = 100
        new_info = self._valid_info()
        new_info["hp"] = 90

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, -10)

    def test_gained_hp(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["hp"] = 100
        new_info = self._valid_info()
        new_info["hp"] = 110

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, 100)

    def test_lost_max_hp(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["max_hp"] = 100
        new_info = self._valid_info()
        new_info["max_hp"] = 90

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, -50)

    def test_gained_max_hp(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["max_hp"] = 100
        new_info = self._valid_info()
        new_info["max_hp"] = 110

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, 50)

    def test_spent_gold(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["gold"] = 100
        new_info = self._valid_info()
        new_info["gold"] = 90

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, 0.5)

    def test_gained_gold(self):
        reward_class = noita_reward.NoitaReward()
        initial_info = self._valid_info()
        initial_info["gold"] = 100
        new_info = self._valid_info()
        new_info["gold"] = 110

        _ = reward_class.update(initial_info)
        reward = reward_class.update(new_info)
        self.assertEqual(reward, 5)

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
        self.assertEqual(reward, 1)


if __name__ == "__main__":
    unittest.main()
