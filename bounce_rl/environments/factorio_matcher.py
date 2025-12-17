# Template match check that factorio is loaded

from pathlib import Path

import numpy as np
from PIL import Image

from bounce_rl.template_matching import TemplateMatcher


class FactorioMatcher:
    """FactorioMatcher provides visual template matching for the Factorio app,
    allowing the environment to know when the app's made certain state transitions."""

    def __init__(self):
        template_dir = Path("bounce_rl/environments/factorio/templates/main_menu")
        images = list(template_dir.glob("**/*.png"))
        images = np.array([np.array(Image.open(i)) for i in images])
        self._template_matcher = TemplateMatcher(images)

    def check_if_on_main_menu(self, image: np.ndarray) -> bool:
        """Check whether the given image is on the game's main menu screen.

        Image should be (H, W, 3) and be scaled to the range [0, 255]."""
        return self._template_matcher.matches(image)
