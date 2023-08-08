import rewards.noita_env as noita_env

import numpy as np

if __name__ == "__main__":
    env = noita_env.NoitaEnv()
    while True:
        pixels, reward, terminated, truncated, info = env.step(env.action_space.sample())
        print(f"mean_pixels: {np.mean(pixels)}, r: {reward}, done: {terminated}, info {info}")
        if terminated:
            env.reset()
