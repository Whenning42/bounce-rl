# AppSession is a container-like object holding a running BounceRL app.
# For each running instance of an app, app session holds a data folder, a virtual
# desktop, and a process.

import subprocess


class AppSession:
    def __init__(self, run_command: str):
        """Creates an AppSession that will run `run_command` once .start_process() is
        called."""
        self._run_command = run_command
        self._desktop = None
        self._folder = None
        self._process = None
        self._time_controller = None

    def start_process() -> subprocess.Process:
        """Launch `run_command` in this AppSession.

        This is it's own function instead of happening automatically in __init__,
        so that callers can copy run-time data into the session folder before
        `run_command` is run."""
        pass

    @property
    def desktop(self):
        return self._desktop

    @property
    def data_folder(self):
        return self._folder

    @property
    def process(self):
        return self._process

    @property
    def time_controller(self):
        return self._time_controller
