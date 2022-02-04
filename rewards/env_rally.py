import rewards
import rewards.art_of_rally
import src.time_writer
import time
import run_configs
from harness import Harness
import gym
import numpy as np

class ArtOfRallyEnv(gym.core.Env):
    def __init__(self):
        X_RES = 960
        Y_RES = 540
        art_of_rally_reward_callback = rewards.art_of_rally.ArtOfRallyReward(plot_output = False)
        run_config = {
            "title": "Art of Rally reward eval",
            "app": "Art of Rally",
            "max_tick_rate": None,
            "x_res": 1920,
            "y_res": 1080,
            "scale": .5,
            "run_rate": 8,
            "pause_rate": .25,
            "step_duration": .250,
        }
        self.run_config = run_config
        app_config = run_configs.LoadAppConfig(run_config["app"])
        harness = Harness(app_config, run_config)
        art_of_rally_reward_callback.attach_to_harness(harness)

        self.harness = harness
        self.reward_callback = art_of_rally_reward_callback
        # TODO: Set up the keyboard.

        self.action_space = gym.spaces.MultiDiscrete([3, 3])
        # Input space is in xlib XK key strings with XK_ left off.
        self.input_space = (("Up", "Down"), ("Left", "Right"))
        self.pixel_shape = (Y_RES, X_RES, 3)
        self.pixel_space = gym.spaces.Box(low = np.zeros(self.pixel_shape),
                                          high = np.ones(self.pixel_shape) * 255,
                                          dtype = np.uint8)
        self.speed_space = gym.spaces.Box(low = -float("inf"), high = float("inf"), shape = (1,))
        self.observation_space = gym.spaces.Dict({"pixels": self.pixel_space, "speed": self.speed_space})

        self.episode_steps = 0
        self.total_steps = 0

    def wait_for_harness_init(self):
        while self.harness.ready == False:
            self.harness.tick()
            time.sleep(.5)

    def render(self):
        print("ArtOfRallyEnv.render is unimplemented.")
        # This environment is always rendered.
        pass

    def reset(self):
        self.wait_for_harness_init()
        self.episode_steps = 0

        self.harness.keyboards[0].set_held_keys(set())
        # NOTE: This will likely fail if the enviroment isn't currently in a race.
        self.harness.keyboards[0].key_sequence(["Escape", "Down", "Return", "Return"])
        time.sleep(2)

        pixels = self.harness.get_screen()
        return {"pixels": pixels, "speed": np.array((0,))}

    def close(self):
        print("ArtOfRallyEnv.close is unimplemented.")
        # This environment can't close itself.
        pass

    def step(self, action):
        self.wait_for_harness_init()

        # Run keyboard presses for the given the gym action.
        key_set = set()
        for i, v in enumerate(action):
            if v == 0:
                continue
            key_set.add(self.input_space[i][v - 1])
        self.harness.keyboards[0].set_held_keys(key_set)

        src.time_writer.SetSpeedup(self.run_config["run_rate"])
        time.sleep(self.run_config["step_duration"] / self.run_config["run_rate"])
        src.time_writer.SetSpeedup(self.run_config["pause_rate"])

        self.episode_steps += 1
        self.total_steps += 1

        done = False
        if self.episode_steps % 480 == 0:
            print("Reached 480 steps, ending episode. Total steps", self.total_steps, flush = True)
            done = True

        pixels = self.harness.get_screen()
        reward, speed, true_reward = self.reward_callback.on_tick()
        state = {"pixels": pixels, "speed": np.array((speed,))}

        info = {}
        info["true_reward"] = true_reward
        if reward is None:
            reward = -1
            info["reward_was_none"] = True

        # print(f"Returning reward {reward}")
        return state, reward, done, info
