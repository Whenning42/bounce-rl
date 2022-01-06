import unittest
from PIL import Image
import numpy as np
from rewards.art_of_rally import *
import torch.nn.functional

class TestArtOfRallyReward(unittest.TestCase):
    def test(self):
        reward = ArtOfRallyReward(device = "cpu", disable_speed_detection = True)

        reverse_roi = np.array(Image.open("test/rewards/golden_reverse.png"))
        penalized_roi = np.array(Image.open("test/rewards/golden_penalized.png"))

        is_reverse_logits = reward.predict_is_reverse(reverse_roi)[0]
        is_penalized_logits = reward.predict_is_penalized(penalized_roi)[0]

        is_reverse_prob = torch.nn.functional.softmax(is_reverse_logits, dim = 0)
        is_penalized_prob = torch.nn.functional.softmax(is_penalized_logits, dim = 0)

        self.assertTrue(.93 <= is_reverse_prob[1] < 1)
        self.assertTrue(.93 <= is_penalized_prob[1] < 1)

if __name__ == "__main__":
    unittest.main()
