import rewards
import rewards.art_of_rally
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
        }
        app_config = run_configs.LoadAppConfig(run_config["app"])
        harness = Harness(app_config, run_config)
        art_of_rally_reward_callback.attach_to_harness(harness)

        self.harness = harness
        self.reward_callback = art_of_rally_reward_callback
        # TODO: Set up the keyboard.

        self.action_space = gym.spaces.MultiDiscrete([3, 3])
        # Input space is in xlib XK key strings with XK_ left off.
        self.input_space = ["Up", "Down", "Left", "Right"]
        self.pixel_shape = (Y_RES, X_RES, 3)
        self.pixel_space = gym.spaces.Box(low = np.zeros(self.pixel_shape), 
                                          high = np.ones(self.pixel_shape) * 255,
                                          dtype = np.uint8)
        self.speed_space = gym.spaces.Box(low = -float("inf"), high = float("inf"), shape = (1,))
        self.observation_space = gym.spaces.Dict({"pixels": self.pixel_space, "speed": self.speed_space})

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
        # TODO: Could consider implementing with a keyboard macro. The hard-part
        # is that the game could reach different states to reset from (main menu,
        # race finish, mid-race, possibly others?)
        print("ArtOfRallyEnv.reset is partially unimplemented.")
        pixels = self.harness.get_screen()
        print(pixels.shape)
        print(pixels.dtype)
        return {"pixels": pixels, "speed": np.array((0,))}

    def close(self):
        print("ArtOfRallyEnv.close is unimplemented.")
        # This environment can't clean itself up.
        pass

    def step(self, action):
        self.wait_for_harness_init()

        # Run keyboard presses for the given the gym action.
        for i, v in enumerate(action):
            if v == 0:
                self.harness.keyboards[0].press_key(self.input_space[2 * i])
                self.harness.keyboards[0].release_key(self.input_space[2 * i + 1])
                print(f"<<< {self.input_space[2 * i]} >>>")
                print(f"    {self.input_space[2 * i + 1]}    ")
            elif v == 1:
                self.harness.keyboards[0].release_key(self.input_space[2 * i])
                self.harness.keyboards[0].release_key(self.input_space[2 * i + 1])
                print(f"    {self.input_space[2 * i]}    ")
                print(f"    {self.input_space[2 * i + 1]}    ")
            elif v == 2:
                self.harness.keyboards[0].release_key(self.input_space[2 * i])
                self.harness.keyboards[0].press_key(self.input_space[2 * i + 1])
                print(f"    {self.input_space[2 * i]}    ")
                print(f"<<< {self.input_space[2 * i + 1]} >>>")

        time.sleep(.3)

        pixels = self.harness.get_screen()
        reward, speed = self.reward_callback.on_tick()
        state = {"pixels": pixels, "speed": np.array((speed,))}

        # Apply action to the harness's keyboard
        done = False
        info = {}
        if reward is None:
            reward = -1
            info["reward_was_none"] = True

        print(f"Returning reward {reward}")
        return state, reward, done, info
