import gym
import rewards.env_rally
import stable_baselines3.common.env_checker
from stable_baselines3 import A2C, DQN, PPO

# Create environment
env = rewards.env_rally.ArtOfRallyEnv()
stable_baselines3.common.env_checker.check_env(env)

_ = input("Waiting for user confirmation of env setup.")

# Instantiate the agent
model = PPO('CnnPolicy', env, verbose=1, device = "cuda:1")
model.learn(total_timesteps=int(2e5))

# Enjoy trained agent
obs = env.reset()
for i in range(3e4):
    action, _states = model.predict(obs, deterministic=True)
    obs, rewards, dones, info = env.step(action)
    # env.render()
