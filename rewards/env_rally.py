import rewards
import rewards.art_of_rally
import src.time_writer
import time
import app_configs
from harness import Harness
import gym
import numpy as np
import callbacks.callbacks as callbacks
import threading
import csv_logger
import os
import PIL.Image
import pathlib

DOWNSAMPLE = 2
STEP_FILE = "steps.csv"
EPISODE_FILE = "episodes.csv"

# Writes features
#   images/*
#   steps.csv
#     - All environment features
#     - Path to pixels
#   episodes.csv
#     - Which episodes have saved pixels
class ArtOfRallyEnv(gym.core.Env):
    def __init__(self, out_dir = None, channel = 0):
        self.out_dir = out_dir
        self.image_dir = os.path.join(self.out_dir, "images")
        self.channel = channel

        pathlib.Path(self.image_dir).mkdir(parents = True, exist_ok = True)
        self.step_logger = csv_logger.CsvLogger(os.path.join(out_dir, STEP_FILE))
        self.episode_logger = csv_logger.CsvLogger(os.path.join(out_dir, EPISODE_FILE))

        X_RES = 960
        Y_RES = 540
        art_of_rally_reward_callback = rewards.art_of_rally.ArtOfRallyReward(plot_output = False)
        screenshot_callback = callbacks.ScreenshotCallback(out_dir = out_dir)
        run_config = {
            "title": "Art of Rally reward eval",
            "app": "Art of Rally (Multi)",
            "max_tick_rate": None,
            "x_res": 1920,
            "y_res": 1080,
            "scale": .5,
            "row_size": 2,
            "run_rate": 8,
            "pause_rate": .25,
            "step_duration": .250,
            "pixels_every_n_episodes": 20
        }
        self.run_config = run_config
        app_config = app_configs.LoadAppConfig(run_config["app"])

        harness = Harness(app_config, run_config, instance = channel)
        art_of_rally_reward_callback.attach_to_harness(harness)
        screenshot_callback.attach_to_harness(harness)

        self.harness = harness
        # Reward callback is called by env.
        self.reward_callback = art_of_rally_reward_callback
        self.screenshot_callback = screenshot_callback

        # Corrsponds to (None, Up, Down), (None, Left, Right)
        self.action_space = gym.spaces.MultiDiscrete([3, 3])
        # Input space is in xlib XK key strings with XK_ left off.
        self.input_space = (("Up", "Down"), ("Left", "Right"))
        self.pixel_shape = (Y_RES // DOWNSAMPLE, X_RES // DOWNSAMPLE, 1)
        self.pixel_space = gym.spaces.Box(low = np.zeros(self.pixel_shape),
                                          high = np.ones(self.pixel_shape) * 255,
                                          dtype = np.uint8)
        self.speed_space = gym.spaces.Box(low = -float("inf"), high = float("inf"), shape = (1,))
        # self.observation_space = gym.spaces.Dict({"pixels": self.pixel_space, "speed": self.speed_space})
        self.observation_space = self.pixel_space

        self.episode = 0
        self.episode_steps = 0
        self.total_steps = 0

        self.env_init = False
        # The setup thread sets self.env_init to True once the setup is finished.
        setup_thread = threading.Thread(target = self._setup_env_async, args = (), kwargs = {})
        setup_thread.start()

    def _wait_for_env_init(self):
        while self.env_init == False:
            time.sleep(.5)
            print("Waiting for env setup")

    def _setup_env_async(self):
        src.time_writer.SetSpeedup(self.run_config["run_rate"], channel = self.channel)

        # Wait for the harness to be initialized
        while self.harness.ready == False:
            self.harness.tick()
            time.sleep(.5)
            print("Waiting for harness")

        # Run the keypresses necessary to get past the menu
        sequence = ((10, "Return"),
                    (.4, "Down"),
                    (.4, "Return"),
                    (.4, "Down"),
                    (.4, "Right"),
                    (.4, "Return"),
                    (.4, "Return"),
                    (15, "Return"),
                    (.4, "Return"),
                    (3, "Return"))
        for t, key in sequence:
            time.sleep(t)
            self.harness.keyboards[0].key_sequence((key,))

        print("Finished launching an episode")
        self.env_init = True

    def render(self):
        print("ArtOfRallyEnv.render is unimplemented.")
        # This environment is always rendered.
        pass

    def episode_saves_pixels(self):
        if self.run_config["pixels_every_n_episodes"] != 0 and \
           self.episode % self.run_config["pixels_every_n_episodes"] == 0:
            return True
        return False

    # Do callers run .reset() before the first episode?
    def reset(self):
        self._wait_for_env_init()
        self.episode_steps = 0
        self.episode += 1

        # Log per episode info.
        to_log = {"episode": self.episode,
                  "first_step": self.total_steps,
                  "episode_has_pixels": self.episode_saves_pixels()}
        self.episode_logger.write_line(to_log)

        # NOTE: This sequence won't reset the env if the game isn't in a race.
        # We handle this by having short enough episodes that agents can't finish
        # the race.
        self.harness.keyboards[0].set_held_keys(set())
        self.harness.keyboards[0].key_sequence(["Escape", "Down", "Return", "Return"])
        time.sleep(2)

        pixels = self.harness.get_screen()[::DOWNSAMPLE, ::DOWNSAMPLE, 0:1]
        return pixels
        # I'd like to return additional state, but doing so doesn't play well with StableBaselines. i.e. DictObservations are compatible with CNN Policies.
        # return {"pixels": pixels, "speed": np.array((0,))}

    def close(self):
        print("Closing ArtOfRallyEnv by killing all running instances.")
        self.harness.kill_subprocesses()
        pass

    def step(self, action):
        self._wait_for_env_init()

        # Run keyboard presses for the given the gym action.
        key_set = set()
        for i, v in enumerate(action):
            if v == 0:
                continue
            key_set.add(self.input_space[i][v - 1])
        self.harness.keyboards[0].set_held_keys(key_set)
        if self.total_steps % 100 == 0:
            self.screenshot_callback.on_tick()

        src.time_writer.SetSpeedup(self.run_config["run_rate"], channel = self.channel)
        time.sleep(self.run_config["step_duration"] / self.run_config["run_rate"])
        src.time_writer.SetSpeedup(self.run_config["pause_rate"], channel = self.channel)

        self.episode_steps += 1
        self.total_steps += 1

        done = False
        if self.episode_steps % 480 == 0:
            print("Reached 480 steps, ending episode. Total steps", self.total_steps, flush = True)
            done = True

        pixels = self.harness.get_screen()[::DOWNSAMPLE, ::DOWNSAMPLE, 0:1]
        features = self.reward_callback.on_tick()

        # Copy eval reward into SB3/Tensorboard integrated reward feature.
        info = {}
        info["true_reward"] = features['eval_reward']

        if features['train_reward'] is None:
            features['train_reward'] = -1
            features["reward_was_none"] = True
        else:
            features["reward_was_none"] = False

        # Log environment features and save pixels if requested.
        to_log = features.copy()
        if self.episode_saves_pixels():
            filename = f"{self.total_steps:08d}.png"
            im = PIL.Image.fromarray(pixels[:, :, 0])
            im.save(os.path.join(self.image_dir, filename))
            to_log["pixels_path"] = filename
        self.step_logger.write_line(to_log)

        # print(f"Returning reward {reward}", flush = True)
        # Should features be returned in info? Probably?
        return pixels, features['train_reward'], done, info
