import math
import unittest

import bounce_desktop
import numpy as np

from bounce_rl.environments.factorio_app import FactorioApp


class TestFactorioApp(unittest.TestCase):
    def test_launch(self):
        """Test that FactorioApp can be launched on a human-viewable desktop."""
        desktop = bounce_desktop.Desktop.create(1000, 600)
        factorio = FactorioApp()
        factorio.begin(desktop)
        # TODO: Once we've got error returns on failed launches, assert launch was successful

    def test_do_finalize_step(self):
        """Test the _do_finalize_step reward calculation."""
        factorio = FactorioApp()
        pixels = np.ones((3, 20, 20), dtype=np.uint8)

        state_0 = {"produced-copper-plate": 10, "produced-iron-plate": 10}
        state_1 = {"produced-copper-plate": 20, "produced-iron-plate": 20}

        factorio._do_finalize_step(pixels, state_0)
        step_1 = factorio._do_finalize_step(pixels, state_1)
        obs, reward, terminated, truncated, info = step_1

        np.testing.assert_array_equal(obs, pixels)
        self.assertAlmostEqual(reward, 2 * (math.log(20) - math.log(10)))
        self.assertFalse(terminated)
        self.assertFalse(truncated)

        # Don't check info for now. Info design is still TBD.


if __name__ == "__main__":
    unittest.main()
