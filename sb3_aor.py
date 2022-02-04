import gym
import rewards.env_rally
import stable_baselines3.common.env_checker
from stable_baselines3 import A2C, DQN, PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecTransposeImage
import stable_baselines3
import os

LOG_PATH = "out/aor_ppo"

# Create environment
env = rewards.env_rally.ArtOfRallyEnv()
# We need to proprocess our environment ourself sicne eval_callback() and PPO.learn() do inconsistent preprocessing.
eval_env = DummyVecEnv([lambda: env])
eval_env = VecTransposeImage(eval_env)

stable_baselines3.common.env_checker.check_env(env)

_ = input("Waiting for user confirmation of env setup.")

callback_nsteps = 20000
eval_callback = stable_baselines3.common.callbacks.EvalCallback(eval_env, eval_freq = callback_nsteps, log_path = LOG_PATH)
checkpoint_callback = stable_baselines3.common.callbacks.CheckpointCallback(save_freq = callback_nsteps, save_path = LOG_PATH)

# Instantiate the agent
model = PPO('MultiInputPolicy', env, verbose=1, device = "cuda:1", tensorboard_log=os.path.join(LOG_PATH, "tensorboard_out"))
model.learn(total_timesteps=int(2e6), callback = [eval_callback, checkpoint_callback])
