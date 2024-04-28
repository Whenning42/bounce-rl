import numpy as np

from bounce_rl.environments.noita import noita_env

if __name__ == "__main__":
    noita_env.NoitaEnv.pre_init()
    env = noita_env.NoitaEnv()

    terminated = False
    while True:
        ret = env.step(
            env.action_space.sample()
        )
        if ret is not None:
            pixels, reward, done, info = ret
            print(
                f"mean_pixels: {np.mean(pixels)}, r: {reward}, done: {done}, info {info}"
            )
        if terminated:
            env.reset()
