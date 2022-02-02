# An class for predicting the current reward for an Art of Rally game running in the Harness.

import harness
import util
import rewards.model_lib as model_lib
import matplotlib.pyplot as plt
import numpy as np
import pathlib
import torch
import os

def _compute_reward(speed, is_reverse, is_penalized):
    is_reverse = is_reverse[1] > is_reverse[0]
    is_penalized = is_penalized[1] > is_penalized[0]

    if None in (speed, is_reverse, is_penalized):
        return None

    if not speed.isnumeric():
        return None

    speed = int(speed)
    speed_mul = 1
    if is_reverse:
        speed_mul *= -1
    penalty = 0
    if is_penalized:
        penalty = 25
    return speed * speed_mul - penalty, speed * speed_mul

class ArtOfRallyReward():
    def __init__(self, plot_output = False, out_dir = None, device = "cuda:1", start_frame = 0, disable_speed_detection = False):
        self.plot_output = plot_output
        self.out_dir = out_dir
        self.device = device
        self.frame = start_frame

        if plot_output:
            pathlib.Path(self.out_dir).mkdir(parents = True, exist_ok = True)

        # The capture methods are initialized in set_harness().
        self.capture_detect_speed = None
        self.capture_is_reverse = None
        self.capture_is_penalized = None

        if disable_speed_detection:
            self.detect_speed_model = None
        else:
            self.detect_speed_model = model_lib.SpeedClassifier() # Will be on "cuda:0"
        self.is_reverse_model = model_lib.BinaryClassifier("models/is_reverse_classifier.pth").to(device)
        self.is_reverse_model.eval()
        self.is_penalized_model = model_lib.BinaryClassifier("models/is_penalized_classifier.pth").to(device)
        self.is_penalized_model.eval()

    def _plot_reward(self, frame, features):
        label = ""
        plot_i = 1
        for feature in features.keys():
            image, prediction = features[feature]
            label += f"{feature}: {prediction}\n"
            if image is not None:
                plt.subplot(2, 2, plot_i)
                plt.imshow(image)
                plot_i += 1

        plt.figure(1)
        plt.suptitle(label)
        plt.savefig(os.path.join(self.out_dir, f"predicted_reward_{frame:05d}.png"))
        plt.clf()

    # Initializes the capture ROI methods using capture instances created in the harness.
    def attach_to_harness(self, harness):
        self.harness = harness

        self.capture_detect_speed = harness.add_capture(util.LoadJSON("annotations.json")["detect_speed"]["roi"]["region"])
        self.capture_is_reverse = harness.add_capture(util.LoadJSON("annotations.json")["is_reverse"]["roi"]["region"])
        self.capture_is_penalized = harness.add_capture(util.LoadJSON("annotations.json")["is_penalized"]["roi"]["region"])

    def predict_detect_speed(self, detect_speed_roi):
        return self.detect_speed_model([detect_speed_roi])

    def predict_is_reverse(self, is_reverse_roi):
        is_reverse_x = is_reverse_roi
        is_reverse_x = self.is_reverse_model.ConvertToDomain(is_reverse_x)
        is_reverse_x = torch.unsqueeze(is_reverse_x, 0)
        is_reverse_x = is_reverse_x.to(self.device)
        return self.is_reverse_model(is_reverse_x)

    def predict_is_penalized(self, is_penalized_roi):
        is_penalized_x = is_penalized_roi
        is_penalized_x = self.is_penalized_model.ConvertToDomain(is_penalized_x)
        is_penalized_x = torch.unsqueeze(is_penalized_x, 0)
        is_penalized_x = is_penalized_x.to(self.device)
        return self.is_penalized_model(is_penalized_x)

    def on_tick(self):
        detect_speed_roi = self.capture_detect_speed()
        if detect_speed_roi.shape != (32, 96, 4):
            # print(detect_speed_roi.shape)
            assert(detect_speed_roi.shape == (16, 48, 4))
            detect_speed_roi = detect_speed_roi.repeat(2, axis = 0).repeat(2, axis = 1)
        # Captured gives (w, h, c) w/ c == 4, BGRA
        is_reverse_roi = util.npBGRAtoRGB(self.capture_is_reverse())
        is_penalized_roi = util.npBGRAtoRGB(self.capture_is_penalized())

        predicted_detect_speed = self.predict_detect_speed(detect_speed_roi)[0]
        predicted_is_reverse = self.predict_is_reverse(is_reverse_roi)[0]
        predicted_is_penalized = self.predict_is_penalized(is_penalized_roi)[0]

        outs = _compute_reward(predicted_detect_speed, predicted_is_reverse, predicted_is_penalized)
        if outs is not None:
            predicted_reward, estimated_speed = outs
        else:
            predicted_reward, estimated_speed = -1, 0

        if self.plot_output:
            self._plot_reward(self.frame, {"detect_speed": [detect_speed_roi, predicted_detect_speed],
                                           "is_reverse": [is_reverse_roi, predicted_is_reverse],
                                           "is_penalized": [is_penalized_roi, predicted_is_penalized],
                                           "reward": [None, predicted_reward]})
        
        self.frame += 1
        return predicted_reward, estimated_speed
