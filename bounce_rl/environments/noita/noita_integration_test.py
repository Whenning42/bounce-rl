import time
import unittest

import numpy as np

from bounce_rl.environments.noita import noita_env


class TestNoitaIntegration(unittest.TestCase):
    def _up_action(self):
        return (np.array([1, 0, 0, 0, 0, 0, 0]), np.array([-0.4, -0.2]))

    def assertNear(self, val, expected, delta):
        self.assertGreater(val, expected - delta)
        self.assertLess(val, expected + delta)

    def test_integration(self):
        RUN_RATE = 0.3
        PAUSE_RATE = 0.3
        STEP_DURATION = 0.05

        noita_env.NoitaEnv.pre_init()
        env = noita_env.NoitaEnv(
            run_config={
                "run_rate": RUN_RATE,
                "pause_rate": PAUSE_RATE,
                "step_duration": STEP_DURATION,
                "scale_mouse_coords": 2,
            },
            seed=1,
        )

        pixels, reward, done, info = env.step(self._up_action())

        # Expect pixels
        mean_pixel, std_pixel = np.mean(pixels), np.std(pixels)
        self.assertNear(mean_pixel, 8.2, 1)
        self.assertNear(std_pixel, 15.3, 2)

        # Expect reward
        self.assertEqual(reward, 0)

        # Expect done
        self.assertFalse(done)

        # Expect info
        expected_infos = {
            "biome": "$biome_coalmine",
            "hp": 100,
            "max_hp": 100,
            "gold": 0,
            "polymorphed": 0,
            "is_alive": True,
        }
        self.assertEqual(info, info | expected_infos)
        x, y = info.get("x", None), info.get("y", None)
        self.assertNear(x, 987, 20)
        self.assertNear(y, 83, 20)
        tick = info.get("tick", None)
        self.assertNear(tick, 280, 500)

        # Expect time controlled pause rate
        time.sleep(2)
        pixels, reward, done, info = env.step(self._up_action())
        new_tick = info.get("tick", None)
        elapsed = new_tick - tick
        expected_elapsed = 2 * 60 * PAUSE_RATE
        self.assertNear(elapsed, expected_elapsed, 0.2 * expected_elapsed)

        # Expect character moved upward
        new_y = info.get("y", None)
        self.assertNear(new_y - y, -50, 30)

        # TODO: Expect mouse in correct spot

        env.close()


if __name__ == "__main__":
    unittest.main()
