# An app integration for Factorio.

import math
from pathlib import Path
from typing import Any

import factorio_state_exporter
from bounce_desktop import Desktop

from bounce_rl.core.app import App
from bounce_rl.core.app_session import AppSession
from bounce_rl.core.gym_types import GymInfo, GymObservation, GymStepTuple
from bounce_rl.environments.factorio_macro import factorio_start_macro
from bounce_rl.input.allowed_inputs import AllowKeys, DisallowKeys
from bounce_rl.input.keys import KEY_ALT_L, KEY_CONTROL_L, KEY_ESCAPE, KEY_GRAVE, FnKeys


class FactorioApp(App):
    def __init__(self):
        self._state_exporter_port = 30111
        self._state_exporter_verbose = False

        self._previous_state: dict[str, Any] = {}
        self._state_reader = factorio_state_exporter.StateReader(
            self._state_exporter_port
        )

    @staticmethod
    def name() -> str:
        """Returns the name of the app used in config."""
        return "Factorio"

    def allowed_input(self) -> AllowKeys:
        """The set of keys agents are allowed to use in the Factorio environment.

        We disable these keys for these reasons:
        - Control: Prevents running ctrl shortcuts e.q. ctrl+q.
        - Escape: Prevents the agent from opening the game's menus.
        - Backtick (Grave): Prevents the agent from opening the console.
        - Alt: Prevents the agent from being able to press Alt+Enter which exits
               full screen mode.
        - All Fn Keys: Prevents opening debug menus/views.
        """
        return DisallowKeys(
            [KEY_CONTROL_L, KEY_ESCAPE, KEY_GRAVE, KEY_ALT_L, FnKeys]
        ).to_allow_list()

    def finalize_step(self, obs: GymObservation) -> GymStepTuple:
        """Get app state at the end of a step and calculate the final step tuple's value."""
        game_state = self._state_reader.get_state()
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

    def post_install(self, session: AppSession) -> None:
        """Install Factorio state export mod into the AppSession's already copied over
        factorio install."""
        factorio_path = Path(session.data_folder()) / "factorio"
        factorio_state_exporter.install_mod(
            factorio_path, self._state_exporter_port, self._state_exporter_verbose
        )

    def begin(self, desktop: Desktop) -> None:
        """Runs the app's launch macro on the given desktop."""
        factorio_start_macro(desktop)

    def supported_resolutions(self) -> list[tuple[int, int]]:
        """Returns a list of resolutions supported by this app."""
        return [(1000, 600)]
