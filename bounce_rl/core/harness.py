import atexit
import json
import logging
import os
import shlex
import signal
import string
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

import numpy as np
import Xlib.protocol
import Xlib.X
import Xlib.XK
from Xlib import display

from bounce_rl.platform.graphics.image_capture import ImageCapture
from bounce_rl.core.input.xtest import Keyboard
from bounce_rl.core.launcher.launcher import Launcher
from bounce_rl.platform.window_connection import WindowConnection
from bounce_rl.utilities import fps_helper, util
from bounce_rl.utilities.paths import project_root

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

window_owners: Dict[int, Any] = {}


def _base_app_env(
    instance: int,
    base_env: Dict[str, str],
    app_config: dict,
    project_root_dir: str,
) -> Dict[str, str]:
    env = base_env.copy()
    if not app_config.get("disable_time_control", False):
        # # NOTE: ld.so only seems to correctly load the multiarch libraries
        # # when we use absolute paths and LD_PRELOAD w/o LD_LIBRARY_PATH.
        # extra_ld_preloads = [
        #     project_root_dir + "/bounce_rl/libs/libtime_control32.so",
        #     project_root_dir + "/bounce_rl/libs/libtime_control64.so",
        # ]
        # env["LD_PRELOAD"] = ":".join([env.get("LD_PRELOAD", ""), *extra_ld_preloads])
        env["TIME_CHANNEL"] = str(instance)

    # Drop the virtualenv path for child process
    if sys.prefix != sys.base_prefix:
        env["PATH"] = ":".join(env["PATH"].split(":")[1:])

    # Only necessary for lutris envs, but is harmless in other envs
    env["LUTRIS_SKIP_INIT"] = "1"
    return env


class Harness(object):
    def __init__(
        self,
        app_config,
        run_config,
        instance=0,
        x_pos: int = 0,
        y_pos: int = 0,
        environment: Optional[dict] = None,
    ):
        logging.debug("Starting harness instance: %s", instance)

        self.app_config = app_config
        self.run_config = run_config
        self.instance = instance
        self.x_pos = x_pos
        self.y_pos = y_pos
        if environment is None:
            environment = {}
        self.environment = environment

        if "init_cmd" in self.app_config:
            os.system(self.app_config["init_cmd"])

        self.fps_helper = fps_helper.Helper(
            throttle_fps=self.run_config.get("max_tick_rate")
        )

        self.display = display.Display()
        self.root_window = self.display.screen().root
        self.root_window.change_attributes(event_mask=Xlib.X.SubstructureNotifyMask)
        self.display.flush()

        self.window = None
        self.keyboard = None
        self.ready = False
        self.proxy_subproc: Optional[Any] = None
        self.launcher = Launcher()

        atexit.register(self._kill_subprocesses)
        self._launch_app()

    def _kill_subprocesses(self):
        self.launcher.kill_instance(self.instance)
        if self.proxy_subproc is not None:
            self.proxy_subproc.kill()
            self.proxy_subproc = None

    def _launch_app(self):
        logging.debug("Opening window.")

        env = os.environ.copy()
        env.update(self.environment)
        env = _base_app_env(
            self.instance, env, self.app_config, project_root_dir=project_root()
        )
        env["PID_OFFSET"] = str(1000 * self.instance)

        directory_template = string.Template(self.app_config.get("directory", ""))
        directory = directory_template.substitute(
            i=self.instance, PROJECT_ROOT=project_root()
        )
        if directory == "":
            directory = None

        windows = self.launcher.launch_app(
            self.instance,
            self.app_config["command"],
            directory,
            json.dumps(env),
            self.app_config["window_title"],
        )

        if len(windows) == 0:
            logging.fatal(
                "Unable to find launched window for instance: %d (timed out)",
                self.instance,
            )
            assert False
        if len(windows) >= 2:
            logging.fatal(
                "Unable to find launched window for instance: %d (too many windows)",
                self.instance,
            )
            assert False
        self._attach(windows[0])

    def _attach(self, window_id):
        window = self.display.create_resource_object("window", window_id)
        window_connection = WindowConnection(self.display, window)
        x = 100 + int(self.run_config["scale"] * self.run_config["x_res"] * self.x_pos)
        y = 100 + int(self.run_config["scale"] * self.run_config["y_res"] * self.y_pos)

        # Note: Configure has to happen before keyboard, since keyboard
        # clicks on the window's expected absolute position to focus
        # the window.
        window.configure(
            x=x,
            y=y,
            width=int(self.run_config["scale"] * self.run_config["x_res"]),
            height=int(self.run_config["scale"] * self.run_config["y_res"]),
        )
        self.display.sync()

        self.window = window
        self.keyboard = Keyboard(
            window_connection,
            self.app_config.get("keyboard_config", {}),
        )
        # Noita environment can't have mouse over a menu item at launch.
        # The enviroment would like to configure this mouse move at launch,
        # but isn't given a callback that runs at the right time.
        self.keyboard.move_mouse(5, 5)
        self.display.flush()
        time.sleep(0.5)
        self.display.flush()

        self._window_capture = ImageCapture(window_connection)
        window_owners[window.id] = self
        self.ready = True

    def cleanup(self):
        """Kills the child app and releases all resources held by this Harness."""
        global window_owners
        atexit.unregister(self._kill_subprocesses)
        self._kill_subprocesses()
        if self.keyboard is not None:
            self.keyboard.cleanup()
        self.display.close()
        for k, v in list(window_owners.items()):
            if v is self:
                del window_owners[k]

    def tick(self):
        """Run the Harness event loop, return False if the attached window is closed."""
        self.fps_helper()

        # Run on_tick if we're connected to a window.
        if self.window is not None:
            for callback in self.run_config.get("on_tick", []):
                callback.on_tick()

        if self.window is None:
            logging.debug("All windows closed. Exiting.")
            return False
        return True

    def get_screen(self) -> np.array:
        assert self._window_capture is not None
        return util.npBGRAtoRGB(self._window_capture.get_image())
