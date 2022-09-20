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
import gin
from multiprocessing import Process

LOCK_OUT = "lock_out"
DOWNSAMPLE = 2
STEP_FILE = "steps.csv"
EPISODE_FILE = "episodes.csv"

# Pixels should be an np array of size (H, W)
def save_im(path, pixels):
    im = PIL.Image.fromarray(pixels)
    im.save(path)

class ResetDecision:
    def __init__(self, steps_per_second):
        self.stuck_seconds = 10
        self.min_average = 3
        self.buf_length = self.stuck_seconds * steps_per_second
        self.vel_buffer = [100] * int(self.buf_length)

    def reset(self):
        self.vel_buffer = [100] * int(self.buf_length)

    def should_reset(self, vel):
        self.vel_buffer = self.vel_buffer[1:]
        self.vel_buffer.append(vel)
        avr = sum(self.vel_buffer) / self.buf_length 
        if avr < self.min_average:
            return True
        return False

# Writes features
#   images/*
#   steps.csv
#     - All environment features
#     - Path to pixels
#   episodes.csv
#     - Which episodes have saved pixels
@gin.configurable
class ArtOfRallyEnv(gym.core.Env):
    # Note: We need gamma to calculate reset penalty.
    def __init__(self, out_dir = None, channel = 0, run_rate = 8, pause_rate = .1, penalty_mode = None, for_test = False, gamma=.99):
        self.max_episode_seconds = 150
        self.out_dir = out_dir
        self.image_dir = os.path.join(self.out_dir, "images")
        self.channel = channel
        self.g = gamma

        pathlib.Path(self.image_dir).mkdir(parents = True, exist_ok = True)
        self.step_logger = csv_logger.CsvLogger(os.path.join(out_dir, STEP_FILE))
        self.episode_logger = csv_logger.CsvLogger(os.path.join(out_dir, EPISODE_FILE))

        X_RES = 960
        Y_RES = 540
        art_of_rally_reward_callback = rewards.art_of_rally.ArtOfRallyReward(plot_output = False)

        run_config = {
            "title": "Art of Rally reward eval",
            "app": "Art of Rally (Multi)",
            "max_tick_rate": None,
            "x_res": 1920,
            "y_res": 1080,
            "scale": .5,
            "row_size": 2,
            "run_rate": run_rate,
            "pause_rate": pause_rate,
            "step_duration": .25, # Record at .125, eval at .25
            "pixels_every_n_episodes": 1
        }
        self.run_config = run_config
        app_config = app_configs.LoadAppConfig(run_config["app"])
        self.max_episode_steps = self.max_episode_seconds // run_config["step_duration"]
        self.steps_per_second = 1 / run_config["step_duration"]

        harness = Harness(app_config, run_config, instance = channel)
        art_of_rally_reward_callback.attach_to_harness(harness)

        self.harness = harness
        # Reward callback is called by env.
        self.reward_callback = art_of_rally_reward_callback

        self.discrete = True
        if self.discrete:
            # Corresponds to (None, Up, Down), (None, Left, Right)
            self.action_space = gym.spaces.MultiDiscrete([3, 3])
        else:
            # Corresponds to (Turn, Brake, Gas)
            self.action_space = gym.spaces.Box(low = np.array((-1, 0, 0)), high = np.array(1, 1, 1))

        # Input space is in xlib XK key strings with XK_ left off.
        self.input_space = ((None, "Up", "Down"), (None, "Left", "Right"))
        self.pixel_shape = (Y_RES // DOWNSAMPLE, X_RES // DOWNSAMPLE, 1)
        self.pixel_space = gym.spaces.Box(low = np.zeros(self.pixel_shape),
                                          high = np.ones(self.pixel_shape) * 255,
                                          dtype = np.uint8)
        self.speed_space = gym.spaces.Box(low = -float("inf"), high = float("inf"), shape = (1,))
        # self.observation_space = gym.spaces.Dict({"pixels": self.pixel_space, "speed": self.speed_space})
        self.observation_space = self.pixel_space

        # Used when penalty_mode = "lock-out"
        self.penalty_mode = penalty_mode
        self.was_penalized = False

        self.episode = 0
        self.episode_steps = 0
        self.total_steps = 0
        self.resetter = ResetDecision(self.steps_per_second)
        self.last_input_time = 0

        if for_test == False:
            self.env_init = False
            # The setup thread sets self.env_init to True once the setup is finished.
            setup_thread = threading.Thread(target = self._setup_env_async, args = (), kwargs = {})
            setup_thread.start()
        else:
            # This path skips navigating to a race screen. Useful for integration
            # testing.
            time.sleep(10)
            self._wait_for_harness_init()
            self.env_init = True

    def _wait_for_env_init(self):
        while self.env_init == False:
            time.sleep(.5)
            print("Waiting for env setup")

    def _wait_for_harness_init(self):
        while self.harness.ready == False:
            self.harness.tick()
            time.sleep(.5)
            print("Waiting for harness")

    def _setup_env_async(self):
        src.time_writer.SetSpeedup(self.run_config["run_rate"], channel = self.channel)
        self._wait_for_harness_init()

        # Run the keypresses necessary to get past the menu
        world = 0
        level = 1
        sequence = ((8, "Return"),
                    (.2, "Down"),
                    (.2, "Return"),
                    *[(.2, "Right")] * world,
                    (.2, "Down"),
                    *[(.2, "Right")] * level,
                    (.2, "Return"),
                    (.2, "Return"),
                    (8, "Return"),
                    (.2, "Return"),
                    (3, "Return"))
        for t, key in sequence:
            time.sleep(t)
            self.harness.keyboards[0].key_sequence((key,))

        print("Finished launching an episode")
        self.env_init = True

    def is_locked_out(self):
        return self.penalty_mode == LOCK_OUT and self.was_penalized

    def render(self):
        print("ArtOfRallyEnv.render is unimplemented.")
        # This environment is always rendered.
        pass

    def episode_saves_pixels(self):
        if self.run_config["pixels_every_n_episodes"] != 0 and \
           self.episode % self.run_config["pixels_every_n_episodes"] == 0:
            return True
        return False

    def recover(self):
        self.resetter.reset()
        self.harness.keyboards[0].set_held_keys(set())
        self.harness.keyboards[0].key_sequence(["Escape", "Down", "Down", "Return", "Return"])
        time.sleep(4)

    def reset(self):
        self._wait_for_env_init()
        self.episode_steps = 0
        self.episode += 1
        self.resetter.reset()

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
        time.sleep(4)

        pixels = self.harness.get_screen()[::DOWNSAMPLE, ::DOWNSAMPLE, 0:1]
        return pixels
        # I'd like to return additional state, but doing so doesn't play well with StableBaselines.
        # i.e. DictObservations are compatible with CNN Policies.
        # return {"pixels": pixels, "speed": np.array((0,))}

    def close(self):
        print("Closing ArtOfRallyEnv by killing all running instances.")
        self.harness.kill_subprocesses()

    def on_input(controller, event):
        now = time.time_ns()
        if now - self.last_input_time < 1e7:
            return
        self.input_logger.write_line(controller.state())

    # 'action' can be set to None to provide no action for this step. This is useful
    # for when a user is controlling the env though a non-env owned keyboard.
    # If 'action' is given as None, logged_action should be given as non-None so that
    # the action taken at this timestep can be logged.
    def step(self, action = None, logged_action = None, perturbed = None):
        self._wait_for_env_init()

        # Run keyboard presses for the given the gym action.
        if action is not None:
            if self.discrete:
                key_set = set((v for v in action if v is not None))
                if self.is_locked_out():
                    key_set = set()
                self.harness.keyboards[0].set_held_keys(key_set)
            else:
                # TODO: Implement agent contorl of an analog input
                assert(False)

        src.time_writer.SetSpeedup(self.run_config["run_rate"], channel = self.channel)
        time.sleep(self.run_config["step_duration"] / self.run_config["run_rate"])
        src.time_writer.SetSpeedup(self.run_config["pause_rate"], channel = self.channel)

        self.episode_steps += 1
        self.total_steps += 1

        done = False
        if self.episode_steps % self.max_episode_steps  == 0:
            print("Reached desired number of steps, ending episode. Total steps", self.total_steps, flush = True)
            done = True

        pixels = self.harness.get_screen()[::DOWNSAMPLE, ::DOWNSAMPLE, 0:1]
        features = self.reward_callback.on_tick()

        # Copy eval reward into SB3/Tensorboard integrated reward feature.
        info = {}
        info["true_reward"] = features['eval_reward']
        info["vel"] = features["vel"]

        if features['train_reward'] is None:
            features['train_reward'] = -1
            features["reward_was_none"] = True
        else:
            features["reward_was_none"] = False

        # Log environment features and save pixels if requested.
        to_log = features.copy()
        if self.episode_saves_pixels():
            filename = f"{self.total_steps:08d}.png"
            path = os.path.join(self.image_dir, filename) 
            save_pixels = pixels[:, :, 0]
            p = Process(target=save_im, args=(path, save_pixels))
            p.start()
            to_log["pixels_path"] = filename

        if perturbed:
            to_log["perturbed"] = True
        else:
            to_log["perturbed"] = False

        if logged_action is None:
            logged_action = action
        to_log["action"] = logged_action

        self.step_logger.write_line(to_log)

        # Lock-out penalty mode application and state update
        if self.is_locked_out():
            print(f"Is locked out, step: {self.total_steps}, train_rew: {features['train_reward']}, vel: {features['vel']}")
            pixels = np.zeros(self.pixel_shape)
        self.was_penalized = features["is_penalized"]

        if not self.is_locked_out():
            reset = self.resetter.should_reset(info["vel"])

        if reset:
            # The discounted value of getting a reward of -1 for the next 'to_go' steps.
            # This is a fitting reward to provide when reseting the environment.

            # On stuck reset:
            # to_go = self.max_episode_steps - self.episode_steps
            # features['train_reward'] = -1/(1-self.g) - (-1/(1-self.g) * self.g**to_go)
            # print("Early reset!")
            # done = True

            # On stuck recover:
            self.recover()

        # Should features be returned in info? Probably?
        return pixels, features['train_reward'], done, info
