# AppEnvironment's take BounceRL App instances and expose them as Gym environments.

import shlex
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from bounce_rl.core.app import App
from bounce_rl.core.app_session import AppSession

# TODO: Replace these placeholders with real types
Action = Any
Observation = Any
Info = Any
Space = Any


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
    def __init__(self, app_cls: type[App], resolution: tuple[int, int]):
        """Initialize AppEnvironment for the given App class and resolution.

        Args:
            app_cls: App subclass to run
            resolution: Desktop resolution as (width, height) tuple
        """
        self.app_cls = app_cls
        self.resolution = resolution
        self._metadata = None
        self.render_mode = None
        self._init()

    def _init(self):
        """Initializes or re-initializes the AppEnvironment.

        Called from __init__ and reset(). Loads config, creates session,
        and delegates to _do_init() for actual environment setup.
        """
        config = load_app_config(self.app_cls.name())
        entrypoint_list = shlex.split(config["entrypoint"])
        session = AppSession(get_sessions_folder(), entrypoint_list, self.resolution)
        self._do_init(self.app_cls, config, session)

    def _do_init(self, app_cls: type[App], config: dict[str, Any], session: AppSession):
        """Starts or restarts the environment for the given app.

        Separated into a helper to support unit testing by allowing
        mock session and config to be injected.

        Args:
            app_cls: App subclass to instantiate
            config: App configuration dictionary
            session: AppSession instance to use
        """
        if hasattr(self, "app") and self.app is not None:
            del self.app
        if hasattr(self, "session") and self.session is not None:
            del self.session

        self.app = app_cls()
        self.app_config = config
        self.session = session

        install_app_from_config(session, config)
        self.app.post_install()
        self.session.start_process()
        self.app.begin(self.session.desktop())
        self.session.time_controller().set_speedup(config.get("pause_speed", 1.0))

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
