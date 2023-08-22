import gym
import rewards.env_rally
import stable_baselines3.common.env_checker
import stable_baselines3
from stable_baselines3.common.vec_env import DummyVecEnv, VecTransposeImage, VecFrameStack, VecMonitor, VecNormalize
import os
import gin
import pathlib
import itertools
import time
import torch
import load_demo
import numpy as np

discrete = False

@gin.configurable
def SAC(out_dir, env, seed = 0):
    return stable_baselines3.SAC('CnnPolicy', env, verbose = 1, device = "cuda:0", tensorboard_log = os.path.join(out_dir, "tensorboard_out"), seed = seed, optimize_memory_usage = True, buffer_size = 80000, learning_starts=0, ent_coef=.1/50, train_freq=4)
    # return stable_baselines3.SAC('CnnPolicy', env, verbose = 1, device = "cuda:0", tensorboard_log = os.path.join(out_dir, "tensorboard_out"), seed = seed, optimize_memory_usage = True, buffer_size = 50000, optimizer_class = torch.optim.SGD, optimizer_kwargs={"lr": 1e-4, "momentum": .9})

load_dir = "analog_demo_0"
def WarmStart(model):
    # Load step file
    # Load input file
    # Load pixels
    # Generate actions from input file and input/step timestamps
    # For each step push last_pixels, curr_pixels, action, reward, is_done to the buffer


@gin.configurable
def run(out_dir = "out/run/", seed = 0, timesteps = 2e6, n_stack = 4):
    train_only = True
    warm_steps = 5000

    out_dir = os.path.join(out_dir, str(seed))
    pathlib.Path(out_dir).mkdir(parents= True, exist_ok = True)

    with open(os.path.join(out_dir, "configs/config.gin"), "w") as f:
        print("Using config:")
        print(gin.config_str())
        f.write(gin.config_str())

    # Create environment
    orig_env = rewards.env_rally.ArtOfRallyEnv(out_dir = out_dir, run_on_init=(not train_only))
    env = VecFrameStack(DummyVecEnv([lambda: orig_env]), n_stack = n_stack)

    eval_env = env
    # Makes episode length and mean reward visible in tensorboard logging.
    env = stable_baselines3.common.vec_env.VecMonitor(env)

    callback_nsteps = 20000
    eval_callback = stable_baselines3.common.callbacks.EvalCallback(eval_env, eval_freq = callback_nsteps, log_path = out_dir)
    checkpoint_callback = stable_baselines3.common.callbacks.CheckpointCallback(save_freq = callback_nsteps, save_path = out_dir)

    # Instantiate the agent.
    model = SAC(out_dir, env)
    print("Initialized SAC model.")
    print("Loading warm start dataset.")
    actions, reward_vals, images, dones, infos = load_demo.LoadDemo("analog_full")

    # Change brake and throttle axes from [0, 1] to [-.95, .95]
    actions[:, 1:3] = actions[:, 1:3] * 1.9 - .95

    # NOTE: The environment doesn't yet provide normalized frames.
    images = (images - images.mean()) / images.std()
    # Apply normalization to reward value. NOTE: The reward value has since been updated to match
    # this renorm. Therefore, if we record a new demo, this will need to not be run on that data.
    reward_vals = 3*reward_vals + 1.2
    # We now re-normalize our reward values to target a cumulative reward in the range of -1 to 1
    # Derived from gamma = .99, expected reward = +-.5
    reward_vals *= 1/50

    for i in range(len(actions)):
        model.replay_buffer.add(images[i], images[i+1], actions[i], reward_vals[i], dones[i], infos = [infos[i]])
    # Left-right flip augment.
    for i in range(len(actions)):
        action = actions[i]
        action[0] *= -1
        image = images[i]
        image = np.flip(image, axis=1)
        next_image = images[i+1]
        next_image = np.flip(next_image, axis=1)
        model.replay_buffer.add(image, next_image, action, reward_vals[i], dones[i], infos = [infos[i]])
    print("Training on warm start dataset.")
    print("Ready to begin learning with operative config: ", gin.operative_config_str())
    # Frame stack breaks check_env?
    # stable_baselines3.common.env_checker.check_env(env)
    if train_only:
        timesteps = warm_steps
    model.learn(total_timesteps = timesteps, callback = [eval_callback, checkpoint_callback], warm_steps = warm_steps)

    # SB3 doesn't close the env after learn call?
    orig_env.close()
    time.sleep(1)

if __name__ == "__main__":
    for seed, n_steps in itertools.product((0,), (4800,)):
        gin.bind_parameter("run.out_dir", f"out/warm_start_2/n_steps_{n_steps}_seed_{seed}")
        gin.bind_parameter("run.seed", seed)
        gin.bind_parameter("SAC.seed", seed)

        run(n_stack = 4)
