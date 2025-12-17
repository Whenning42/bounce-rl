import unittest

import numpy as np
from PIL import Image

from bounce_rl.environments.factorio_matcher import FactorioMatcher


class TestFactorioLoaded(unittest.TestCase):
    def test_correct_not_loaded(self):
        test_im = np.array(
            Image.open("bounce_rl/environments/factorio/templates/loading/loading.png")
        )

        fl = FactorioMatcher()
        self.assertEqual(fl.check_if_on_main_menu(test_im), False)

    def test_correct_loaded(self):
        test_im = np.array(
            Image.open(
                "bounce_rl/environments/factorio/templates/main_menu/template_0_2_0_66.png"
            )
        )

        fl = FactorioMatcher()
        self.assertEqual(fl.check_if_on_main_menu(test_im), True)


if __name__ == "__main__":
    unittest.main()
