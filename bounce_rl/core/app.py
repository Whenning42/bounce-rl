# Instances of the App class implement app-specific BounceRL integrations.
# TODO: Figure out how Apps communicate any set up steps they need to run.

from abc import ABC, abstractmethod

from bounce_desktop import Desktop

from bounce_rl.core.gym_types import GymObservation, GymStepTuple


class App(ABC):
    @abstractmethod
    def finalize_step(self, obs: GymObservation) -> GymStepTuple:
        """Get app state at the end of a step and calculate the final step tuple's
        value."""
        ...

    @abstractmethod
    def start(self, desktop: Desktop) -> None:
        """Runs the app's launch macro on the given desktop."""
        ...

    @abstractmethod
    def supported_resolutions(self) -> list[tuple[int, int]]:
        """Returns a list of resolutions supported by this app."""
        ...
