import multiprocessing as mp
from typing import Any, Callable, Dict, Optional

import gym
import numpy as np
from stable_baselines3.common.vec_env.base_vec_env import CloudpickleWrapper


def _worker(
    remote: mp.connection.Connection,
    parent_remote: mp.connection.Connection,
    env_fn_wrapper: CloudpickleWrapper,
) -> None:
    parent_remote.close()
    env = env_fn_wrapper.var()
    reset_info: Optional[Dict[str, Any]] = {}
    while True:
        try:
            cmd, data = remote.recv()
            if cmd == "step":
                observation, reward, done, info = env.step(data)
                remote.send((observation, reward, done, info, reset_info))
            elif cmd == "reset":
                maybe_options = {"options": data[1]} if data[1] else {}
                observation = env.reset(seed=data[0], **maybe_options)
                remote.send(observation)
            elif cmd == "close":
                env.close()
                remote.close()
                break
            elif cmd == "get_spaces":
                remote.send((env.observation_space, env.action_space))
            elif cmd == "env_method":
                method = getattr(env, data[0])
                remote.send(method(*data[1], **data[2]))
            elif cmd == "hasattr":
                remote.send(hasattr(env, data))
            else:
                raise NotImplementedError(f"`{cmd}` is not implemented in the worker")
        except EOFError:
            break


class SubprocEnv(gym.Env):
    """
    Creates a multiprocess vectorized wrapper for multiple environments, distributing each environment to its own
    process, allowing significant speed up when the environment is computationally complex.

    For performance reasons, if your environment is not IO bound, the number of environments should not exceed the
    number of logical cores on your CPU.

    .. warning::

        Only 'forkserver' and 'spawn' start methods are thread-safe,
        which is important when TensorFlow sessions or other non thread-safe
        libraries are used in the parent (see issue #217). However, compared to
        'fork' they incur a small start-up cost and have restrictions on
        global variables. With those methods, users must wrap the code in an
        ``if __name__ == "__main__":`` block.
        For more information, see the multiprocessing documentation.

    :param env_fns: Environments to run in subprocesses
    :param start_method: method used to start the subprocesses.
           Must be one of the methods returned by multiprocessing.get_all_start_methods().
           Defaults to 'forkserver' on available platforms, and 'spawn' otherwise.
    """

    def __init__(
        self, env_fn: Callable[[], gym.Env], start_method: Optional[str] = None
    ):
        self.waiting = False
        self.closed = False

        if start_method is None:
            # Fork is not a thread safe method (see issue #217)
            # but is more user friendly (does not require to wrap the code in
            # a `if __name__ == "__main__":`)
            forkserver_available = "forkserver" in mp.get_all_start_methods()
            start_method = "forkserver" if forkserver_available else "spawn"
        ctx = mp.get_context(start_method)

        self.remote, self.work_remote = ctx.Pipe()
        args = (self.work_remote, self.remote, CloudpickleWrapper(env_fn))
        # daemon=True: if the main process crashes, we should not cause things to hang
        self.process = ctx.Process(target=_worker, args=args, daemon=True)  # type: ignore[attr-defined]
        self.process.start()
        self.work_remote.close()

        self.remote.send(("get_spaces", None))
        self.observation_space, self.action_space = self.remote.recv()

    # Do we need the async API for SB3 integration?
    # def step_async(self, action: np.ndarray) -> None:
    #     self.remote.send(("step", action))
    #     self.waiting = True
    #
    # def step_wait(self):
    #     result = self.remote.recv()
    #     self.waiting = False
    #     obs, rews, dones, infos, self.reset_infos = result
    #     return obs, rews, dones, infos

    def step(self, action: np.ndarray) -> tuple:
        self.remote.send(("step", action))
        self.waiting = True
        result = self.remote.recv()
        self.waiting = False
        obs, rew, done, info, self.reset_info = result
        return obs, rew, done, info

    def reset(self, seed=None):
        self.remote.send(("reset", (0, None)))
        result = self.remote.recv()
        return result  # type: ignore[assignment]

    def close(self) -> None:
        if self.closed:
            return
        if self.waiting:
            self.remote.recv()
        self.remote.send(("close", None))
        self.process.join()
        self.closed = True

    def env_hasattr(self, attr_name: str) -> bool:
        self.remote.send(("hasattr", attr_name))
        return self.remote.recv()

    def env_method(
        self,
        method_name: str,
        *method_args,
        **method_kwargs,
    ) -> Any:
        self.remote.send(("env_method", (method_name, method_args, method_kwargs)))
        return self.remote.recv()
