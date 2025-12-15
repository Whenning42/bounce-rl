"""Test helper for creating fake AppSession instances in unit tests."""

import os
import subprocess
import tempfile

from libtimecontrol import TimeController

from bounce_rl.core.app_session import AppSession


class FakeAppSession(AppSession):
    """Minimal fake AppSession for testing install_app_from_config.

    Provides just enough interface to test file installation without
    creating real Desktop instances or launching processes.
    """

    def __init__(
        self,
        sessions_folder: str,
        run_command: list[str] | None = None,
        resolution: tuple[int, int] | None = None,
        visible: bool = False,
    ):
        """Create a fake session with a temp folder under sessions_folder.

        Args:
            sessions_folder: Parent directory for creating temp session folder
        """
        self._run_command = run_command
        self._folder = tempfile.TemporaryDirectory(prefix=sessions_folder)
        self._time_controller = TimeController()
        self._process = None

    def desktop(self) -> None:
        return None

    def data_folder(self) -> str:
        return self._folder.name

    def process(self) -> subprocess.Popen | None:
        return self._process

    def time_controller(self) -> TimeController:
        return self._time_controller

    def __del__(self):
        if hasattr(self, "_folder") and self._folder is not None:
            self._folder.cleanup()

    def start_process(self) -> subprocess.Popen:
        # Crash if FakeAppSession.start_process() is called on a
        # fake app session that wasn't constructed with a run command.
        assert self._run_command is not None
        self._process = subprocess.Popen(
            self._run_command,
            env=os.environ | self._time_controller.child_flags(),
        )
        return self._process
