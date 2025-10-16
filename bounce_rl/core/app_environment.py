# AppEnvironment's take BounceRL App instances and expose them as Gym environments.

from typing import Any

import numpy as np

# TODO: Replace these placeholders with real types
Action = Any
Observation = Any
Info = Any
App = Any
Space = Any


class AppEnvironment:
    def __init__(self, app: App):
        self._app = app
        self._metadata = None
        self.render_mode = None

    def reset(
        self, seed: int | None, options: dict[str, Any]
    ) -> tuple[Observation, Info]:
        pass

    def step(self, action: Action) -> tuple[Observation, float, bool, bool, Info]:
        pass

    def render(self) -> None | np.ndarray:
        pass

    def close(self) -> None:
        pass

    @property
    def action_space(self) -> Space:
        pass

    @property
    def observation_space(self) -> Space:
        pass
