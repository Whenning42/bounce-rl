# AppSession is a container-like object holding a running BounceRL app.
# For each running instance of an app, app session holds a data folder, a virtual
# desktop, and a process.
#
# TODO: Make subprocess clean-up robust. i.e. use a subprocess reaper.
# TODO: Make temp folder clean-up robust. i.e. use something
# like ephemeral_directory() implemented in libtimecontrol (currently
# it only has a C implementation, no bindings).
# TODO: Clean up the subprocess at an appropriate time.
# TODO: Unit tests should maybe use mock desktops.

import os
import subprocess
import tempfile

import bounce_desktop
import libtimecontrol

from bounce_rl.input.input_processor import InputProcessor


class AppSession:
    def __init__(
        self,
        sessions_folder: str,
        run_command: list[str],
        resolution: tuple[int, int],
        visible=False,
    ):
        """Creates an AppSession that will run `run_command` once .start_process() is
        called.

        Args:
            sessions_folder: Parent directory for creating temp session folder
            run_command: Command to execute (list of command parts)
            resolution: Desktop resolution as (width, height) tuple
        """
        self._run_command = run_command
        self._desktop = bounce_desktop.Desktop.create(
            resolution[0], resolution[1], visible
        )
        self._folder = tempfile.TemporaryDirectory(prefix=sessions_folder)
        self._process = None
        self._time_controller = libtimecontrol.TimeController()
        self._input_processor = InputProcessor(resolution[0], resolution[1])

    def __del__(self):
        # Only clean up the process if it's actually been started.
        if self._process is not None:
            self._process.kill()
        if self._folder is not None:
            self._folder.cleanup()

    def _popen(self, *args, **kwargs) -> subprocess.Popen:
        """A wrapper around subprocess.Popen that's used by start_process. We use this
        to mock subprocess calls in unit tests."""
        return subprocess.Popen(*args, **kwargs)

    def start_process(self) -> subprocess.Popen:
        """Launch `run_command` in this AppSession.

        This is it's own function instead of happening automatically in __init__,
        so that callers can copy run-time data into the session folder before
        `run_command` is run."""
        self._process = self._popen(
            self._run_command,
            env=os.environ
            | self._desktop.get_desktop_env()
            | self._time_controller.child_flags(),
            cwd=self.data_folder(),
        )

    def desktop(self) -> bounce_desktop.Desktop:
        return self._desktop

    def data_folder(self) -> str:
        return self._folder.name

    def process(self) -> subprocess.Popen | None:
        return self._process

    def time_controller(self) -> libtimecontrol.TimeController:
        return self._time_controller

    def input_processor(self) -> InputProcessor:
        return self._input_processor
