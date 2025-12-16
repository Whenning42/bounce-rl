import time

from bounce_rl.core.app_environment import AppEnvironment
from bounce_rl.environments.factorio_app import FactorioApp

if __name__ == "__main__":
    env = AppEnvironment(FactorioApp, (1000, 600), render_mode="human")

    N = 60
    for i in range(N):
        step_res = env.step(env.action_space.sample())
        print(f"Run 1/2, step {i}/{N}")
        time.sleep(0.2)

    print("Finished test!")
