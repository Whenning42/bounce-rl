# An class for predicting the current reward for an Art of Rally game running in the Harness.

import harness
import model_lib
import matplotlib.pyplot as plt
import os

class ArtOfRallyReward():
    def __init__(self, plot_output = False, out_dir = None):
        self.plot_output = plot_output
        self.out_dir = out_dir

        self.capture_detect_speed = Harness.CaptureRegion(util.LoadJSON("annotations.json")["detect_speed"]["roi"]["region"])
        self.capture_is_reverse = Harness.CaptureRegion(util.LoadJSON("annotations.json")["is_reverse"]["roi"]["region"])
        self.capture_is_penalized = Harness.CaptureRegion(util.LoadJSON("annotations.json")["is_penalized"]["roi"]["region"])

        self.detect_speed_model = model_lib.SpeedClassifier(), # Will be on "cuda:0"
        self.is_reverse_model = model_lib.BinaryClassifier("models/is_reverse_classifier.pth", "cuda:1"),
        self.is_penalized_model = model_lib.BinaryClassifier("models/is_penalized_classifier.pth", "cuda:1")}
        self.frame = 0

    def _compute_reward(speed, is_reverse, is_penalized):
        if None in (speed, is_reverse, is_penalized):
            return None

        speed_mul = 1
        if is_reverse:
            speed_mul *= -1
        penalty = 0
        if is_penalized:
            penalty = 50
        return speed * speed_mul - penalty

    def _plot_reward(frame, features):
        label = ""
        plot_i = 1
        for feature in features.keys():
            image, prediction = features[feature]
            if image is not None:
                plt.subplot(2, 2, plot_i)
                plt.imshow(image)

            label += f"{feature}: {prediction}\n"
            plot_i += 1
        label += f"reward: {reward}"

        plt.figure(1)
        plt.suptitle(label)
        plt.savefig(os.path.join(self.out_dir, f"predicted_reward_{frame:05d}.png"))
        plt.clf()

    def on_frame(self):
        detect_speed_roi = self.capture_detect_speed()
        is_reverse_roi = self.capture_is_reverse()
        is_penalized_roi = self.capture_is_penalized()

        predicted_detect_speed = self.detect_speed_model(detect_speed_roi)
        predicted_is_reverse = self.is_reverse_model(is_reverse_roi)
        predicted_is_penalized = self.is_penalized_model(is_penalized_roi)

        predicted_reward = _compute_reward(predicted_detect_speed, predicted_is_reverse, predicted_is_penalized)
        if plot_output:
            _plot_reward(self.frame, {"detect_speed": [detect_speed_roi, predicted_detect_speed],
                                      "is_reverse": [is_reverse_roi, predicted_is_reverse],
                                      "is_penalized": [is_penalized_roi, predicted_is_penalized],
                                      "reward": [None, predicted_reward]}
        self.frame += 1
