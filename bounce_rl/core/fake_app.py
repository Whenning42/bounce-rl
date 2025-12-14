from bounce_desktop import Desktop

from bounce_rl.core.app import App
from bounce_rl.core.gym_types import GymObservation, GymStepTuple


def fake_app_config() -> dict:
    return {"apps": [{"name": "fake_app", "entrypoint": "pwd"}]}


class FakeApp(App):
    """A fake App implementation to use in unit tests."""

    @staticmethod
    def name() -> str:
        return "fake_app"

    def finalize_step(self, obs: GymObservation) -> GymStepTuple:
        pass

    def post_install(self) -> None:
        pass

    def begin(self, desktop: Desktop) -> None:
        pass

    def supported_resolutions(self) -> list[tuple[int, int]]:
        return [(640, 480)]
