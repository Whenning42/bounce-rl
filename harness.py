import atexit
import logging
import os
import re
import shlex
import signal
import string
import subprocess
import sys
import time

import numpy as np
import psutil
import Xlib.protocol
import Xlib.X
import Xlib.XK
from Xlib import Xatom, display

import fps_helper
import image_capture
import keyboard
import src.containers.container as container
import util

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')


REOPEN_CLOSED_WINDOWS = False

window_owners = {}


def handle_error(*args):
    window_id = args[0].resource_id.id
    if window_id in window_owners:
        window_owners[window_id].window_closed(window_id)
    else:
        logging.debug("Orphan window closed: %s", window_id)


# Caller has to unpack the property return value.
# For "_NET_WM_PID" property, it's an array of ints. For other types I'm not sure.
def query_window_property(display, window, property_name, property_type):
    property_name_atom = display.get_atom(property_name)
    try:
        result = window.get_full_property(property_name_atom, property_type)
        if result:
            return result.value
    except Xlib.error.BadWindow:
        return -1


# A no-op error handler.
def suppress_error(*args):
    pass


class Harness(object):
    def __init__(
        self,
        app_config,
        run_config,
        instance=0,
        x_pos: int = 0,
        y_pos: int = 0,
        environment: dict = None,
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

        window_count = 1
        self.window_title = self.app_config["window_title"]
        self.tick_start = time.time()
        self.display = display.Display()
        self.display.set_error_handler(handle_error)  # Python XLib handler
        image_capture.ImageCapture.set_error_handler(
            suppress_error
        )  # Screen capture library has no need to throw errors

        self.root_window = self.display.screen().root
        self.root_window.change_attributes(event_mask=Xlib.X.SubstructureNotifyMask)
        self.display.flush()

        self.subprocess_pids = []
        self.pid_mapper = None
        atexit.register(self.kill_subprocesses)

        for i in range(window_count):
            self.open_new_window()

        self.windows = [None for _ in range(window_count)]
        self.keyboards = [None for _ in range(window_count)]
        self.captures = []
        self.full_window_capture = None
        self.ready = False

    def kill_subprocesses(self):
        logging.debug("kill subprocess")
        for pid in self.subprocess_pids:
            logging.debug("Killing subprocess: %s", pid)
            os.kill(pid, signal.SIGKILL)

    def window_closed(self, window_id):
        global window_owners
        del window_owners[window_id]

        for i in range(len(self.windows)):
            if self.windows[i].id == window_id:
                self.windows[i] = -1
                self.keyboards[i] = None
                if REOPEN_CLOSED_WINDOWS:
                    self.open_new_window()
                return
        # Make sure that window_closed is called on a window with a connection
        assert False

    def open_new_window(self):
        env = os.environ.copy()
        env.update(self.environment)

        if not self.app_config.get("disable_time_control", False):
            env["LD_PRELOAD"] = "libtime_control.so"
        if sys.prefix != sys.base_prefix:
            # Drop the virtualenv path for child process
            env["PATH"] = ":".join(env["PATH"].split(":")[1:])
        if self.app_config.get("use_x_proxy", False):
            env["DISPLAY"] = ":1"
        # Only necessary for lutris envs, but is harmless in other envs
        env["LUTRIS_SKIP_INIT"] = "1"
        if self.instance is not None:
            env["TIME_CHANNEL"] = str(self.instance)

        split_command = shlex.split(self.app_config["command"])
        directory_template = string.Template(self.app_config["directory"])
        directory = directory_template.substitute(i=self.instance)
        if directory == "":
            directory = None
        unshare_pid, cmd_pid, pid_mapper = container.launch_process_container(
            split_command, directory, env, pid_offset=1000 * self.instance
        )
        logging.debug("Started subprocess: %s", unshare_pid)
        self.subprocess_pids.append(unshare_pid)
        self.pid_mapper = pid_mapper

    # Return True if the window's process is a descendant any of the child_pids.
    def is_owned(self, window, child_pids):
        # Note: Requires the application to set _NET_WM_PID annotations on the window.
        window_pid_result = query_window_property(
            self.display, window, "_NET_WM_PID", Xatom.CARDINAL
        )
        assert (
            window_pid_result is not None
        ), "Harness requires the running window manager to implement _NET_WM_PID annotations."
        window_pid = window_pid_result[0]
        logging.debug("Got window pid: %s", window_pid)
        # The _NET_WM_PID will be a pid in the container namespace. We need to map it
        # back to the host pid namespace.
        host_pid = self.pid_mapper.get(window_pid)
        window_ps = psutil.Process(host_pid)

        is_owned = False
        # is_owned = self.instance * 1000 + 8 == window_pid
        while window_ps is not None:
            if window_ps.pid in child_pids:
                is_owned = True
                break
            window_ps = window_ps.parent()

        logging.debug("Is owned query: instance: %s, window: %s, window_pid: %s, mapped_pid: %s, is_owned: %s", self.instance, window.id, window_pid, host_pid, is_owned)
        return is_owned

    def get_all_windows_with_name(name, parent, matches):
        try:
            for child in parent.query_tree().children:
                wm_name = child.get_wm_name()
                if wm_name is not None:
                    if isinstance(wm_name, bytes):
                        wm_name = wm_name.decode("utf-8")
                if wm_name is not None and re.match(name, wm_name):
                    matches.append(child)
                matches = Harness.get_all_windows_with_name(name, child, matches)
            return matches
        except:
            return matches

    def connect_to_windows(self):
        time.sleep(1)
        global window_owners
        open_windows = Harness.get_all_windows_with_name(
            self.app_config["window_title"], self.root_window, []
        )
        if self.app_config.get("process_mode", "") == "separate":
            owned_windows = open_windows
        else:
            owned_windows = [
                w for w in open_windows if self.is_owned(w, self.subprocess_pids)
            ]
        if len(owned_windows) == 0:
            logging.debug(
                "Harness looking for window with title: %s",
                self.app_config["window_title"],
            )

        owned_ids = [w.id for w in owned_windows]
        for w in owned_windows:
            if w not in self.windows:
                if None not in self.windows:
                    logging.error(
                        "Harness %s found too many seemingly owned windows: %s", self.instance, owned_ids
                    )
                    break

                loc = self.windows.index(None)
                x = int(
                    self.run_config["scale"] * self.run_config["x_res"] * self.x_pos
                )
                y = int(
                    self.run_config["scale"] * self.run_config["y_res"] * self.y_pos
                )
                # Note: Configure has to happen before keyboard, since keyboard
                # clicks on the window's expected absolute position to focus
                # the window.
                w.configure(
                    x=x,
                    y=y,
                    width=int(self.run_config["scale"] * self.run_config["x_res"]),
                    height=int(self.run_config["scale"] * self.run_config["y_res"]),
                )
                self.display.sync()

                self.windows[loc] = w
                self.keyboards[loc] = keyboard.Keyboard(
                    self.display,
                    w,
                    x,
                    y,
                    self.app_config.get("keyboard_config", {}),
                    instance=self.instance,
                )
                # Noita environment can't have mouse over a menu item at launch.
                # The enviroment would like to configure this mouse move at launch,
                # but isn't given a callback that runs at the right time.
                self.keyboards[loc].move_mouse(5, 5)
                self.display.flush()
                time.sleep(0.5)
                self.display.flush()

                self.display.flush()
                self.full_window_capture = self.add_capture(
                    (0, 0, self.run_config["x_res"], self.run_config["y_res"])
                )
                window_owners[w.id] = self

        if None not in self.windows:
            self.ready = True

    def cleanup(self):
        global window_owners
        atexit.unregister(self.kill_subprocesses)
        self.kill_subprocesses()
        for kb in self.keyboards:
            kb.cleanup()
        self.display.close()
        for k, v in list(window_owners.items()):
            if v is self:
                del window_owners[k]

    def tick(self):
        self.fps_helper()

        if None in self.windows:
            self.connect_to_windows()

        self.tick_start = time.time()

        # Run on_tick only if we're connected to all windows.
        if None not in self.windows:
            callbacks = self.run_config.get("on_tick")
            if callbacks is not None:
                for callback in callbacks:
                    callback.on_tick()

        if self.windows.count(-1) == len(self.windows):
            logging.debug("All windows closed. Exiting.")
            return False
        return True

    def get_screen(self, instance=0) -> np.array:
        return util.npBGRAtoRGB(self.full_window_capture())

    def _focus_windows(self):
        for w in self.windows:
            if w is None:
                continue
            for detail in [Xlib.X.NotifyAncestor, Xlib.X.NotifyVirtual]:
                e = Xlib.protocol.event.FocusIn(
                    display=self.display,
                    window=w,
                    detail=detail,
                    mode=Xlib.X.NotifyNormal,
                )
                self.display.send_event(w, e)
                w.change_attributes(event_mask=Xlib.X.FocusChangeMask)
        self.display.flush()

    def _disable_user_input(self):
        for w in range(len(self.windows)):
            self.windows[w].change_attributes(event_mask=Xlib.X.FocusChangeMask)
            self.display.flush()

    def perform_actions(self, keymap):
        self._focus_windows()
        # self._disable_user_input()
        # for w in self.windows:
        #    self.capture.FocusAndIgnoreAllEvents(w.id)
        for keyboard in self.keyboards:
            if keyboard is None:
                continue
            keyboard.set_keymap(keymap)

    # Takes a ROI of format ("x", "y", "w", "h") and returns a function that can
    # be called to capture a np array of the pixels in that region.
    # TODO: Add support for running from multiple instances.
    def add_capture(self, region):
        INSTANCE = 0
        region = [round(c * self.run_config["scale"]) for c in region]
        x, y, w, h = region
        capture = image_capture.ImageCapture(x, y, w, h)
        self.captures.append(capture)
        # Use a default argument to force the lambda not to capture a reference to self.
        return lambda id=self.windows[INSTANCE].id: capture.get_image(id)

    def pause(self):
        pgid = os.getpgid(self.subprocess_pids[0])
        os.killpg(pgid, signal.SIGSTOP)

    def resume(self):
        pgid = os.getpgid(self.subprocess_pids[0])
        os.killpg(pgid, signal.SIGCONT)
