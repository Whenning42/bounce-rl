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

        is_reverse_logits = reward.predict_is_reverse(reverse_roi)
        is_penalized_logits = reward.predict_is_penalized(penalized_roi)
        print("Is reverse pred: ", torch.nn.functional.softmax(is_reverse_logits))
        print("Is penalized pred: ", torch.nn.functional.softmax(is_reverse_logits))

if __name__ == "__main__":
    unittest.main()
