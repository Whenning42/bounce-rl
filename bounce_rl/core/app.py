# Instances of the App class implement app-specific BounceRL integrations.

from abc import ABC, abstractmethod

from bounce_desktop import Desktop

from bounce_rl.core.gym_types import GymObservation, GymStepTuple
from bounce_rl.input.allowed_inputs import AllowKeys


class App(ABC):
    @staticmethod
    @abstractmethod
    def name() -> str:
        """Returns the name of the app used to select it from the BounceRL config."""
        ...

    @abstractmethod
    def allowed_input(self) -> AllowKeys:
        """Returns the set of key presses that this environment supports.
        Keys may be disallowed for example to prevent agents from accidentally quitting
        or opening settings menus."""
        ...

    @abstractmethod
    def finalize_step(self, obs: GymObservation) -> GymStepTuple:
        """Get app state at the end of a step and calculate the final step tuple's
        value."""
        ...

    @abstractmethod
    def post_install(self) -> None:
        """Runs install logic after copying app files from install config.

        For example, Factorio generates instance-specific mod settings and installs
        its state-export mod in post_install."""
        ...

    @abstractmethod
    def begin(self, desktop: Desktop) -> None:
        """Runs the app's launch macro on the given desktop."""
        ...

    @abstractmethod
    def supported_resolutions(self) -> list[tuple[int, int]]:
        """Returns a list of resolutions supported by this app."""
        ...
