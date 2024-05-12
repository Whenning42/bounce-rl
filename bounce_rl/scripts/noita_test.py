import argparse
import time

import numpy as np

from bounce_rl.environments.noita import noita_env

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--manual_control", type=bool, default=False)
    args = parser.parse_args()

    xproxy = True
    step = True
    if args.manual_control:
        xproxy = False
        step = False

    noita_env.NoitaEnv.pre_init()
    env = noita_env.NoitaEnv(
        run_config={"run_rate": 1, "use_x_proxy": xproxy}, seed=args.seed
    )

    terminated = False
    while True:
        if not step:
            time.sleep(10)
            continue

        ret = env.step(env.action_space.sample())
        if ret is not None:
            pixels, reward, done, info = ret
            print(
                f"mean_pixels: {np.mean(pixels)}, r: {reward}, done: {done}, info {info}"
            )
        if done:
            env.reset()
