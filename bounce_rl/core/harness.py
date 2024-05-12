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

from bounce_rl.core.image_capture import image_capture
from bounce_rl.core.keyboard import keyboard
from bounce_rl.core.launcher.launcher import Launcher
from bounce_rl.utilities import fps_helper, util
from bounce_rl.utilities.paths import project_root

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")


REOPEN_CLOSED_WINDOWS = False

window_owners: Dict[int, Any] = {}


def handle_error(*args):
    window_id = args[0].resource_id.id
    if window_id in window_owners:
        window_owners[window_id].on_window_closed(window_id)
    else:
        logging.debug("Orphan window closed: %s", window_id)


# Caller has to unpack the property return value.
# For "_NET_WM_PID" property, it's an array of ints. For other types I'm not sure.
def query_window_property(display, window, property_name, property_type) -> List[int]:
    property_name_atom = display.get_atom(property_name)
    try:
        result = window.get_full_property(property_name_atom, property_type)
        if result:
            return list(result.value)
        else:
            return []
    except Xlib.error.BadWindow:
        return [-1]


# A no-op error handler.
def suppress_error(*args):
    pass


def base_app_env(
    instance: int,
    base_env: Dict[str, str],
    app_config: dict,
    project_root_dir: str,
) -> Dict[str, str]:
    env = base_env.copy()
    if not app_config.get("disable_time_control", False):
        # NOTE: ld.so only seems to correctly load the multiarch libraries
        # when we use absolute paths and LD_PRELOAD w/o LD_LIBRARY_PATH.
        extra_ld_preloads = [
            project_root_dir + "/bounce_rl/libs/libtime_control32.so",
            project_root_dir + "/bounce_rl/libs/libtime_control64.so",
        ]
        env["LD_PRELOAD"] = ":".join([env.get("LD_PRELOAD", ""), *extra_ld_preloads])
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
        self.display.set_error_handler(handle_error)  # Python XLib handler
        image_capture.ImageCapture.set_error_handler(
            suppress_error  # Screen capture library has no need to throw errors
        )

        self.root_window = self.display.screen().root
        self.root_window.change_attributes(event_mask=Xlib.X.SubstructureNotifyMask)
        self.display.flush()

        self.window = None
        self.keyboard = None
        self.full_window_capture = None
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

    def _launch_x_proxy(self) -> int:
        host_x_display = os.environ.get("DISPLAY", ":0")
        proxy_x_display = 10 + self.instance

        command = (
            f'xauth add :{proxy_x_display} .  "$(xauth list | grep $(hostname) '
            f"| grep '{host_x_display}' | awk '{{print $3}}')\""
        )
        subprocess.run(command, shell=True)

        subprocess.run(shlex.split(f"rm -f /tmp/.X11-unix/X{proxy_x_display}"))
        self.proxy_subproc = subprocess.Popen(
            [
                "python",
                f"{project_root()}/bounce_rl/x_multiseat/proxy.py",
                "--proxy_display",
                f"{proxy_x_display}",
                "--real_display",
                host_x_display,
            ]
        )
        time.sleep(0.1)
        return proxy_x_display

    def _launch_app(self):
        logging.debug("Opening window.")

        env = os.environ.copy()
        env.update(self.environment)
        env = base_app_env(
            self.instance, env, self.app_config, project_root_dir=project_root()
        )
        env["PID_OFFSET"] = str(1000 * self.instance)

        directory_template = string.Template(self.app_config.get("directory", ""))
        directory = directory_template.substitute(
            i=self.instance, PROJECT_ROOT=project_root()
        )
        if directory == "":
            directory = None

        if self.run_config.get("use_x_proxy", False):
            proxy_display = self._launch_x_proxy()
            env["DISPLAY"] = f":{proxy_display}"

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
        x = int(self.run_config["scale"] * self.run_config["x_res"] * self.x_pos)
        y = int(self.run_config["scale"] * self.run_config["y_res"] * self.y_pos)

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
        self.keyboard = keyboard.Keyboard(
            self.display,
            window,
            x,
            y,
            self.app_config.get("keyboard_config", {}),
            instance=self.instance,
        )
        # Noita environment can't have mouse over a menu item at launch.
        # The enviroment would like to configure this mouse move at launch,
        # but isn't given a callback that runs at the right time.
        self.keyboard.move_mouse(5, 5)
        self.display.flush()
        time.sleep(0.5)
        self.display.flush()

        self.full_window_capture = self._add_capture(
            (0, 0, self.run_config["x_res"], self.run_config["y_res"])
        )
        window_owners[window.id] = self
        self.ready = True

    # Takes a ROI of format ("x", "y", "w", "h") and returns a function that can
    # be called to capture a np array of the pixels in that region.
    def _add_capture(self, region):
        region = [round(c * self.run_config["scale"]) for c in region]
        x, y, w, h = region
        capture = image_capture.ImageCapture(x, y, w, h)
        # Use a default argument to force the lambda not to capture a reference to self.
        return lambda id=self.window.id: capture.get_image(id)

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

    def get_screen(self, instance=0) -> np.array:
        assert self.full_window_capture is not None
        return util.npBGRAtoRGB(self.full_window_capture())

    def pause(self):
        pgid = os.getpgid(self.subprocess_pid)
        os.killpg(pgid, signal.SIGSTOP)

    def resume(self):
        pgid = os.getpgid(self.subprocess_pid)
        os.killpg(pgid, signal.SIGCONT)

    def on_window_closed(self, window_id):
        global window_owners
        del window_owners[window_id]

        if self.window.id == window_id:
            self.window = None
            self.keyboard = None
            if REOPEN_CLOSED_WINDOWS:
                self._launch_app()
            return
        assert False
