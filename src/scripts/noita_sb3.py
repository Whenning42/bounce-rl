import gym
import stable_baselines3.common.env_checker
import stable_baselines3
from stable_baselines3.common.vec_env import DummyVecEnv, VecTransposeImage, VecFrameStack, VecMonitor
import rewards.noita_env
import os
import gin
import pathlib
import itertools
import time
import torch

discrete = False

@gin.configurable
def PPO(out_dir, env, seed = 0, n_steps = 2048, ent_coef = .01):
    return stable_baselines3.PPO('CnnPolicy', env, verbose = 1, device = "cuda:0", tensorboard_log = os.path.join(out_dir, "tensorboard_out"), seed = seed, n_steps = n_steps, ent_coef = ent_coef)

@gin.configurable
def run(out_dir = "out/run/", seed = 0, timesteps = 1e6, n_stack = 3):
    out_dir = os.path.join(out_dir, str(seed))
    pathlib.Path(out_dir).mkdir(parents= True, exist_ok = True)

    # Step duration is set to 0.25 in NoitaEnv.
    orig_env = rewards.noita_env.NoitaEnv(out_dir = out_dir)
    env = VecFrameStack(DummyVecEnv([lambda: orig_env]), n_stack = n_stack)

    eval_env = env
    # Makes episode length and mean reward visible in tensorboard logging.
    env = stable_baselines3.common.vec_env.VecMonitor(env)

    callback_nsteps = 30000
    eval_callback = stable_baselines3.common.callbacks.EvalCallback(eval_env, eval_freq = callback_nsteps, log_path = out_dir, n_eval_episodes = 3, deterministic=False)
    checkpoint_callback = stable_baselines3.common.callbacks.CheckpointCallback(save_freq = callback_nsteps, save_path = out_dir)

    # Instantiate the agent.
    model = PPO(out_dir, env)

    print("Ready to train with operative config: ", gin.operative_config_str())
    # Frame stack breaks check_env?
    # stable_baselines3.common.env_checker.check_env(env)
    model.learn(total_timesteps = timesteps, callback = [eval_callback, checkpoint_callback])
    exit()

    # SB3 doesn't close the env after learn call?
    orig_env.close()
    time.sleep(1)

# Move config into a gin file if it grows too big. See sb3_aor.py for an example.
if __name__ == "__main__":
    for seed, n_steps in itertools.product((0,), (4000,)):
        gin.bind_parameter("run.out_dir", f"out/noita_sb3_ppo_no_reg/n_steps_{n_steps}_seed_{seed}")
        gin.bind_parameter("run.seed", seed)
        gin.bind_parameter("PPO.seed", seed)
        gin.bind_parameter("PPO.n_steps", n_steps)

        run(n_stack = 4)
