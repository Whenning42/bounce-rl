import rewards.noita_env as noita_env

if __name__ == '__main__':
    env = noita_env.NoitaEnv()
    while True:
        env.step(env.action_space.sample())
