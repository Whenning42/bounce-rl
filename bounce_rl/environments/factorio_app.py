# An app integration for Factorio.

import math
from typing import Any

from factorio_state_exporter import StateReader

from bounce_rl.core.app import App
from bounce_rl.core.gym_types import GymInfo, GymObservation, GymStepTuple


class FactorioApp(App):
    def __init__(self):
        self._previous_state: dict[str, Any] = {}

    def finalize_step(self, obs: GymObservation) -> GymStepTuple:
        """Get app state at the end of a step and calculate the final step tuple's value."""
        game_state = StateReader.get_state()
        return self._do_finalize_step(obs, game_state)

    def _do_finalize_step(
        self, obs: GymObservation, game_state: dict[str, Any]
    ) -> GymStepTuple:
        """Calculate the step tuple using observation and game state.

        Reward is based on production progress: log difference of copper and iron plates.
        """
        terminated = False
        truncated = False
        info: GymInfo = game_state

        # Calculate reward based on copper and iron production
        def production_reward(d: dict[str, Any]) -> float:
            produced = (
                d.get("produced-copper-plate", 0),
                d.get("produced-iron-plate", 0),
            )
            clamped = (max(v, 1) for v in produced)
            return sum(math.log(v) for v in clamped)

        cur_val = production_reward(game_state)
        last_val = production_reward(self._previous_state)
        reward = cur_val - last_val

        self._previous_state = game_state
        return (obs, reward, terminated, truncated, info)

    def start(self, desktop) -> None:
        """Runs the app's launch macro on the given desktop.

        TODO: Implement the Factorio start sequence here.
        This should launch Factorio and get it to a state where the agent can begin
        interacting with the game.
        """
        # TODO: Implement Factorio launch macro
        pass

    def supported_resolutions(self) -> list[tuple[int, int]]:
        """Returns a list of resolutions supported by this app."""
        return [(1000, 600)]
