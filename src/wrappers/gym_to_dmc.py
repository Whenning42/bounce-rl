import dm_env
import numpy as np

class GymToDmc(dm_env.Environment):
    def __init__(self, gym_env):
        self.gym_env = gym_env
        self.is_first = True
        self.last_pixels = None

    def action_spec(self):
        # Does this require the gym action space to be Box?
        # DO_NOT_SUBMIT: Add a unit test for the Discrete case.

        act_space = self.gym_env.action_space
        minimum = getattr(act_space, 'low', -np.inf)
        maximum = getattr(act_space, 'high', np.inf)
        return dm_env.specs.BoundedArray(shape = self.gym_env.action_space.shape, \
                                         dtype = self.gym_env.action_space.dtype, \
                                         minimum = minimum,
                                         maximum = maximum,
                                         name = 'action')

    def observation_spec(self):
        obs_space = self.gym_env.observation_space
        # DO_NOT_SUBMIT: Add a unit test for envs with gym obs spaces without low and high.
        minimum = getattr(obs_space, 'low', -np.inf)
        maximum = getattr(obs_space, 'high', np.inf)
        return {'pixels': dm_env.specs.BoundedArray(shape = obs_space.shape, \
                                         dtype = obs_space.dtype, \
                                         minimum = minimum, \
                                         maximum = maximum, \
                                         name = 'observation')}

    # reward_spec uses the default implementation (specifies a single float).

    # discount_spec uses the default implementation (specifies a single float between 0 and 1).

    def reset(self):
        obs = self.gym_env.reset()
        self.is_first = False

        self.last_pixels = obs
        obs = {'pixels': obs}
        return dm_env.TimeStep(step_type = dm_env.StepType.FIRST, \
                               reward = None,
                               observation = obs,
                               discount = None)

    # Note: Starts a run if the environment has just been constructed and reset() hasn't been
    # called.
    def step(self, action):
        obs, reward, is_done, info = self.gym_env.step(action)
        discount = float(1)

        step_type = dm_env.StepType.MID
        if self.is_first:
            step_type = dm_env.StepType.FIRST
            reward = None
            discount = None
            self.is_first = False

        if is_done:
            step_type = dm_env.StepType.LAST
            discount = float(0)
            self.is_first = True

        self.last_pixels = obs
        obs = {'pixels': obs}
        return dm_env.TimeStep(step_type = step_type, \
                               reward = reward, \
                               observation = obs, \
                               discount = discount)

    def close(self):
        self.gym_env.close()

    # DrQ-V2 VideoRecorder expects the env to implement env.physics.render or
    # env.render().
    def render(self):
        return self.last_pixels
