import atexit
import image_capture
import fps_helper
import numpy as np
import os
import subprocess
import signal
import time
import shlex
import keyboard
import util
from model import *

from Xlib import display
import Xlib.X
import Xlib.XK
import Xlib.protocol

REOPEN_CLOSED_WINDOWS = False

x_tiles = 1
y_tiles = 1

window_owners = {}

def handle_error(*args):
    window_id = args[0].resource_id.id
    if window_id in window_owners:
        window_owners[window_id].window_closed(window_id);
    else:
        print("Orphan window closed:", window_id)

# A no-op error handler.
def suppress_error(*args):
    pass

class Harness(object):
    def __init__(self, app_config, run_config):
        self.app_config = app_config
        self.run_config = run_config
        self.fps_helper = fps_helper.Helper(throttle_fps \
                                        = self.run_config.get("max_tick_rate"))

        window_count = x_tiles * y_tiles
        self.window_title = self.app_config["window_title"]
        self.tick_start = time.time()
        # Pass in the display here
        self.display = display.Display()
        self.display.set_error_handler(handle_error) # Python XLib handler
        image_capture.ImageCapture.set_error_handler(suppress_error) # Screen capture library has no need to throw errors

        self.root_window = self.display.screen().root
        self.root_window.change_attributes(event_mask = Xlib.X.SubstructureNotifyMask)
        self.display.flush()

        self.subprocess_pids = []
        atexit.register(self.kill_subprocesses)

        for i in range(window_count):
            self.open_new_window()

        self.windows = [None for _ in range(window_count)]
        self.keyboards = [None for _ in range(window_count)]
        self.captures = []
        self.full_screen_capture = None
        self.ready = False

    def kill_subprocesses(self):
        for pid in self.subprocess_pids:
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
        assert(False)

    def open_new_window(self):
        split_command = shlex.split(self.app_config["command"])
        process = subprocess.Popen(split_command, cwd=self.app_config["directory"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.subprocess_pids.append(process.pid)

    def GetAllWindowsWithName(name, parent, matches):
        for child in parent.query_tree().children:
            #if child.get_wm_name() is not None:
            #    print("Child: " + child.get_wm_name())
            if child.get_wm_name() == name:
                matches.append(child)
            matches = Harness.GetAllWindowsWithName(name, child, matches)
        return matches

    def connect_to_windows(self):
        time.sleep(1)
        global window_owners
        open_windows = Harness.GetAllWindowsWithName(self.app_config["window_title"], self.root_window, [])

        if len(open_windows) == 0:
            print("Still looking for window with title: ", self.app_config["window_title"])

        for w in open_windows:
            if w not in self.windows:
                # Make sure we haven't opened too many instances
                assert(None in self.windows)
                loc = self.windows.index(None)
                self.windows[loc] = w
                self.keyboards[loc] = keyboard.Keyboard(self.display, w)
                print(w)
                print(hex(w.id))
                subprocess.Popen(["i3-msg", "[id=" + hex(w.id) + "]", "floating", "enable;", \
                                                                      "border", "pixel", "0"])
                self.display.flush()
                time.sleep(.5)
                self.display.flush()
                w.configure(x = self.run_config["x_res"] * (loc % x_tiles), \
                            y = self.run_config["y_res"] * (loc // x_tiles), \
                            width = self.run_config["x_res"], height = self.run_config["y_res"])
                self.display.flush()
                self.full_screen_capture = self.add_capture((0, 0, self.run_config["x_res"], self.run_config["y_res"]))
                window_owners[w.id] = self

        if not None in self.windows:
            self.ready = True

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
            print("All windows closed. Exiting.")
            return False

        return True

    def get_screen(self, instance = 0):
        return util.npBGRAtoRGB(self.full_screen_capture())

    def _focus_windows(self):
        for w in self.windows:
            if w is None:
                continue
            # I'm unsure which detail to send so I send all of them to be cautious, Xlib.X.NotifyInferior, Xlib.X.NotifyNonlinear, Xlib.X.NotifyNonlinearVirtual, Xlib.X.NotifyPointer, Xlib.X.NotifyPointerRoot, Xlib.X.NotifyDetailNone]
            for detail in [Xlib.X.NotifyAncestor, Xlib.X.NotifyVirtual]:
                e = Xlib.protocol.event.FocusIn(display=self.display, window=w, detail=detail, mode=Xlib.X.NotifyNormal)
                self.display.send_event(w, e)
                w.change_attributes(event_mask=Xlib.X.FocusChangeMask)
        self.display.flush()

    def _disable_user_input(self):
        for w in range(len(self.windows)):
            self.windows[w].change_attributes(event_mask=Xlib.X.FocusChangeMask)
            self.display.flush()

    def perform_actions(self, keymap):
        self._focus_windows()
        #self._disable_user_input()
        #for w in self.windows:
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
        return lambda: capture.get_image(self.windows[INSTANCE].id)

