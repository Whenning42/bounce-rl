# Train a PPO agent on Noita using stable-baselines3.
# Note: Requires changes in our forked SB3 repo.
# The repo's at: https://github.com/Whenning42/stable-baselines3
# and tuple action space support is added as of commit 4fedd69.

import argparse
import itertools
import os
import pathlib
import sys
import time

import gin
import stable_baselines3
import stable_baselines3.common.env_checker
from stable_baselines3.common.vec_env import VecFrameStack

from bounce_rl.environments.noita import noita_env
from bounce_rl.gym.env.pool_vec_env import PoolVecEnv

parser = argparse.ArgumentParser(description="Train a PPO agent on Noita.")
parser.add_argument("--out_dir", type=str, required=True)
parser.add_argument("--exp_name", type=str, required=True)

discrete = False


@gin.configurable
def PPO(tensorboard_out_dir, env, seed=0, n_steps=2048, ent_coef=0.01):
    return stable_baselines3.PPO(
        "CnnPolicy",
        env,
        verbose=1,
        device="cuda:0",
        tensorboard_log=tensorboard_out_dir,
        seed=seed,
        n_steps=n_steps,
        normalize_values=True,
        ent_coef=ent_coef,
        n_epochs=4,
        target_kl=0.03,
        learning_rate=4e-5,
        batch_size=128,
    )


@gin.configurable
def run(
    env_out_dir,
    tensorboard_out_dir,
    checkpoint_out_dir,
    logs_out_dir,
    n_steps=2048,
    seed=0,
    timesteps=1e6,
    n_stack=4,
    num_envs=4,
):
    # Step duration is set to 0.125 in NoitaEnv.
    noita_env.NoitaEnv.pre_init(num_envs=num_envs)
    env_fns = []
    for i in range(num_envs):
        env_out = env_out_dir + f"/env_{i}"
        env_fns.append(
            lambda i=i, env_out=env_out: noita_env.NoitaEnv(
                out_dir=env_out,
                skip_startup=True,
                x_pos=i % 2,
                y_pos=i // 2,
                instance=i,
            )
        )
    env = VecFrameStack(
        PoolVecEnv(env_fns, n=num_envs, k=num_envs - 1), n_stack=n_stack
    )
    # Makes episode length and mean reward visible in tensorboard logging.
    env = stable_baselines3.common.vec_env.VecMonitor(env)

    callback_nsteps = 30000
    eval_callback = stable_baselines3.common.callbacks.EvalCallback(
        env,
        eval_freq=callback_nsteps,
        log_path=logs_out_dir,
        n_eval_episodes=3,
        deterministic=False,
    )
    checkpoint_callback = stable_baselines3.common.callbacks.CheckpointCallback(
        save_freq=callback_nsteps, save_path=checkpoint_out_dir
    )

    # Instantiate the agent.
    model = PPO(tensorboard_out_dir, env, n_steps=n_steps, seed=seed)

    print("Ready to train with operative config: ", gin.operative_config_str())
    # Frame stack breaks check_env?
    # stable_baselines3.common.env_checker.check_env(env)
    model.learn(
        total_timesteps=timesteps, callback=[eval_callback, checkpoint_callback]
    )
    exit()

    # SB3 doesn't close the env after learn call?
    time.sleep(1)


# Move config into a gin file if it grows too big. See sb3_aor.py for an example.
if __name__ == "__main__":
    args = parser.parse_args()
    # Output folder structure:
    #  out/exp_name/
    #  out/exp_name/step_data
    #  out/tensorboard/exp_name
    #  out/exp_name/checkpoints
    #  out/exp_name/logs

    exp_dir = os.path.join(args.out_dir, args.exp_name)
    pathlib.Path(exp_dir).mkdir(parents=True, exist_ok=False)
    tensorboard_dir = os.path.join(args.out_dir, "tensorboard", args.exp_name)
    pathlib.Path(tensorboard_dir).mkdir(parents=True, exist_ok=False)
    checkpoint_dir = os.path.join(exp_dir, "checkpoints")
    pathlib.Path(checkpoint_dir).mkdir()
    log_dir = os.path.join(exp_dir, "logs")
    pathlib.Path(log_dir).mkdir()

    run(exp_dir, tensorboard_dir, checkpoint_dir, log_dir, n_steps=1000)
