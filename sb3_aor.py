import gym
import rewards.env_rally
import stable_baselines3.common.env_checker
import stable_baselines3
from stable_baselines3.common.vec_env import DummyVecEnv, VecTransposeImage, VecFrameStack, VecMonitor
import os
import gin
import pathlib
import itertools
import time
import torch
from torch.profiler import profile, record_function, ProfilerActivity

discrete = False

@gin.configurable
def PPO(out_dir, env, seed = 0, n_steps = 2048, ent_coef = .01):
    return stable_baselines3.PPO('CnnPolicy', env, verbose = 1, device = "cuda:0", tensorboard_log = os.path.join(out_dir, "tensorboard_out"), seed = seed, n_steps = n_steps, ent_coef = ent_coef)

@gin.configurable
def SAC(out_dir, env, seed = 0, ent_coef = .1):
    return stable_baselines3.SAC('CnnPolicy', env, verbose = 1, device = "cuda:0", tensorboard_log = os.path.join(out_dir, "tensorboard_out"), seed = seed, optimize_memory_usage = True, buffer_size = 200000, learning_starts=5000, ent_coef = ent_coef, train_freq=50, gradient_steps=50)
    # return stable_baselines3.SAC('CnnPolicy', env, verbose = 1, device = "cuda:0", tensorboard_log = os.path.join(out_dir, "tensorboard_out"), seed = seed, optimize_memory_usage = True, buffer_size = 50000, optimizer_class = torch.optim.SGD, optimizer_kwargs={"lr": 1e-4, "momentum": .9})

@gin.configurable
def run(out_dir = "out/run/", seed = 0, timesteps = 2e6, n_stack = 4):
    out_dir = os.path.join(out_dir, str(seed))
    pathlib.Path(out_dir).mkdir(parents= True, exist_ok = True)

    with open(os.path.join(out_dir, "config.gin"), "w") as f:
        print("Using config:")
        print(gin.config_str())
        f.write(gin.config_str())

    # Create environment
    gamma = .985
    orig_env = rewards.env_rally.ArtOfRallyEnv(out_dir = out_dir, gamma=gamma)
    env = VecFrameStack(DummyVecEnv([lambda: orig_env]), n_stack = n_stack)

    eval_env = env
    # Makes episode length and mean reward visible in tensorboard logging.
    env = stable_baselines3.common.vec_env.VecMonitor(env)

    callback_nsteps = 30000
    eval_callback = stable_baselines3.common.callbacks.EvalCallback(eval_env, eval_freq = callback_nsteps, log_path = out_dir, n_eval_episodes = 3)
    checkpoint_callback = stable_baselines3.common.callbacks.CheckpointCallback(save_freq = callback_nsteps, save_path = out_dir)

    # Instantiate the agent.
    if discrete:
        model = PPO(out_dir, env)
    else:
        model = SAC(out_dir, env, ent_coef = .1 * (1-gamma))

    print("Ready to train with operative config: ", gin.operative_config_str())
    # Frame stack breaks check_env?
    # stable_baselines3.common.env_checker.check_env(env)
    model.learn(total_timesteps = timesteps, callback = [eval_callback, checkpoint_callback])
    exit()

    # SB3 doesn't close the env after learn call?
    orig_env.close()
    time.sleep(1)

gin.parse_config_file('config.gin')

if __name__ == "__main__":
    for seed, n_steps in itertools.product((0,), (4800,)):
        gin.bind_parameter("run.out_dir", f"out/w_ent_coef2/n_steps_{n_steps}_seed_{seed}")
        gin.bind_parameter("run.seed", seed)
        gin.bind_parameter("PPO.seed", seed)
        gin.bind_parameter("SAC.seed", seed)
        gin.bind_parameter("PPO.n_steps", n_steps)

        run(n_stack = 4)
