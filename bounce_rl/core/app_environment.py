# AppEnvironment's take BounceRL App instances and expose them as Gym environments.

import shlex
import shutil
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
import yaml

from bounce_rl.core.app import App
from bounce_rl.core.app_session import AppSession
from bounce_rl.core.gym_types import GymAction, GymInfo, GymObservation
from bounce_rl.input import gym_input


def get_sessions_folder() -> str:
    """Get the session folder location in user's home directory.

    Returns:
        Path to the sessions folder
    """
    return str(Path.home() / ".local" / "share" / "bounce_rl")


def load_app_config(app_name: str, config_path: str | None = None) -> dict[str, Any]:
    """Load app configuration from bounce_rl/config.yaml.

    Args:
        app_name: Name of the app to load config for
        config_path: Path to load the BounceRL config from. If not given, defaults to
                     loading the default BounceRL config "bounce_rl/config.yaml".

    Returns:
        Dictionary containing app configuration e.g.
        {"name": "Factorio", "entrypoint": "...", ...}

    Raises:
        FileNotFoundError: If config.yaml doesn't exist
        KeyError: If app with given name not found in config
        yaml.YAMLError: If config file is malformed
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    apps = config.get("apps", [])
    for app in apps:
        if app.get("name") == app_name:
            return app
    raise KeyError(f"App '{app_name}' not found in config")


def install_app_from_config(session: AppSession, config: dict[str, Any]) -> None:
    """Copy files and folders specified in app's install config to session folder.

    Args:
        session: AppSession with data_folder() to copy files into
        config: App configuration with optional 'install' key

    The install config should be a dict or list of dicts with 'from' and 'to' keys.
    'from' paths are absolute or relative to current directory.
    'to' paths are relative to session.data_folder()
    """
    # Handle both single dict and list of dicts
    install_spec = config.get("install", [])
    if isinstance(install_spec, dict):
        install_items = [install_spec]
    else:
        install_items = install_spec

    session_folder = Path(session.data_folder())
    for item in install_items:
        src = Path(item["from"])
        dst = session_folder / item["to"]

        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dst)
        elif src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            raise FileNotFoundError(f"Install source not found: {src}")


class AppEnvironment:
    def __init__(
        self,
        app_cls: type[App],
        resolution: tuple[int, int],
        session_cls: type = AppSession,
        config_path: str | None = None,
    ):
        """Initialize AppEnvironment for the given App class and resolution.

        Args:
            app_cls: App subclass to run
            resolution: Desktop resolution as (width, height) tuple
        """
        self.app_cls = app_cls
        self.resolution = resolution
        self._metadata = None
        self.render_mode = None
        self.session_cls = session_cls
        self.config_path = config_path
        self._init()

    def _init(self):
        """Initializes or re-initializes the AppEnvironment.

        Called from __init__ and reset(). Loads the config and creates an AppSession,
        then installs and starts the app.
        """
        self.config = load_app_config(self.app_cls.name(), self.config_path)
        self.session = self.session_cls(
            get_sessions_folder(),
            shlex.split(self.config["entrypoint"]),
            self.resolution,
        )

        self.app = self.app_cls()
        self._allowed_input = self.app.allowed_input()
        install_app_from_config(self.session, self.config)
        self.app.post_install()
        self.session.start_process()
        self.app.begin(self.session.desktop())
        self.session.time_controller().set_speedup(self.config.get("pause_speed", 1.0))

    def reset(
        self, seed: int | None, options: dict[str, Any]
    ) -> tuple[GymObservation, GymInfo]:
        self._init()
        return self.step(gym_input.no_op_gym_action())

    def step(
        self, action: GymAction
    ) -> tuple[GymObservation, float, bool, bool, GymInfo]:
        # TODO
        pass

    def render(self) -> None | np.ndarray:
        # TODO
        pass

    def close(self) -> None:
        if hasattr(self, "app") and self.app is not None:
            del self.app
        if hasattr(self, "session") and self.session is not None:
            del self.session

    @property
    def action_space(self) -> gym.Space:
        return gym_input.action_space(self.resolution[0], self.resolution[1])

    @property
    def observation_space(self) -> gym.Space:
        return gym.spaces.Box(
            0,
            255,
            (3, self.resolution[0], self.resolution[1]),
            dtype=np.uint8,
        )
