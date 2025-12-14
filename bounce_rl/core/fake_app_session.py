"""Test helper for creating fake AppSession instances in unit tests."""

import os
import subprocess
import tempfile

from libtimecontrol import TimeController


class FakeAppSession:
    """Minimal fake AppSession for testing install_app_from_config.

    Provides just enough interface to test file installation without
    creating real Desktop instances or launching processes.
    """

    def __init__(
        self,
        sessions_folder: str,
        run_command: list[str] | None = None,
        resolution: tuple[int, int] | None = None,
    ):
        """Create a fake session with a temp folder under sessions_folder.

        Args:
            sessions_folder: Parent directory for creating temp session folder
        """
        self._run_command = run_command
        self._folder = tempfile.TemporaryDirectory(prefix=sessions_folder)
        self._time_controller = TimeController()

    def desktop(self) -> None:
        return None

    def data_folder(self) -> str:
        return self._folder.name

    def process(self) -> None:
        return None

    def time_controller(self) -> None:
        return self._time_controller

    def __del__(self):
        if hasattr(self, "_folder") and self._folder is not None:
            self._folder.cleanup()

    def start_process(self) -> subprocess.Popen:
        self._process = subprocess.Popen(
            self._run_command,
            env=os.environ | self._time_controller.child_flags(),
        )
