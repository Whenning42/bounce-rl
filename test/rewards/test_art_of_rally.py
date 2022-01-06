import unittest
from PIL import Image
import numpy as np
from rewards.art_of_rally import *

class TestArtOfRallyReward(unittest.TestCase):
    def test(self):
        reward = ArtOfRallyReward(device = "cpu", disable_speed_detection = True)

        reverse_roi = np.array(Image.open("test/rewards/golden_reverse.png"))
        penalized_roi = np.array(Image.open("test/rewards/golden_penalized.png"))

        print("Reverse max val:", np.max(reverse_roi))
        print("Reverse min val:", np.min(reverse_roi))
        print("Reverse shape:", reverse_roi.shape)

        print("Is reverse pred: ", reward.predict_is_reverse(reverse_roi))
        print("Is penalized pred: ", reward.predict_is_penalized(penalized_roi))

if __name__ == "__main__":
    unittest.main()
