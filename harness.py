import atexit
import image_capture
import numpy as np
import os
import subprocess
import signal
import time
import shlex
from model import *

from Xlib import display
import Xlib.X
import Xlib.XK
import Xlib.protocol

REOPEN_CLOSED_WINDOWS = False

# Skyrogue config.
# Skyrogue tries launches steam if the working directory isn't the game's directory.
# directory = "/home/william/.local/share/Steam/steamapps/common/Sky Rogue"
# command = "./skyrogue.x86"
# window_title = "Sky Rogue"

# MC config.
directory = "./"
command = open("minecraft_command.txt").read()
window_title = "Minecraft 1.16.3"

# Firefox config.
# directory = "./"
# command = "firefox"
# window_title = "Mozilla Firefox"

fps = 24
x_res = 720
y_res = 480
x_tiles = 1
y_tiles = 1

class Keyboard(object):
    PRESS = 1
    RELEASE = -1
    SHIFT_MOD = 1
    CTRL_MOD = 4
    ALT_MOD = 8

    def __init__(self, display, window):
        self.last_keymap = np.zeros(84)
        self.focused_window = window
        self.display = display

    def _mask_keymap(keymap):
        keymap[0] = 0 # reserved
        keymap[58] = 0 # caps lock
        keymap[69] = 0 # num lock
        keymap[70] = 0 # scroll lock
        return keymap

    def _assert_keymap_is_masked(keymap):
        assert(keymap[0] == 0)
        assert(keymap[58] == 0)
        assert(keymap[69] == 0)
        assert(keymap[70] == 0)

    def keycode_for_key_name(key_name):
        keycode = Xlib.XK.string_to_keysym(key_name)
        assert(keycode is not None)
        return keycode - 8 # Convert X11 keycodes to linux ones

    # Toggles keys to
    def set_keymap(self, keymap):
        keymap = Keyboard._mask_keymap(keymap)
        # keymap is an 84 element long 0-1 array corresponding to linux keycodes 0-83
        # Sets a scancode bitmap encoding
        toggled_keys = keymap - self.last_keymap
        modifier = Keyboard.modifier_state(keymap)
        for i in range(84):
            if toggled_keys[i] == 1:
                self.press_key(i, modifier)
            elif toggled_keys[i] == -1:
                self.release_key(i, modifier)
        self.last_keymap = keymap

    def modifier_state(keymap):
        # LShift keycode: 50 state: 1
        # RShift keycode: 62 state: 1
        # LCtrl  keycode: 37 state: 4
        # RCtrl  keycode:105 state: 4 # Not in our keymap
        # LAlt   keycode: 64 state: 8
        # RAlt   keycode:108 state: 8 # Not in our keymap
        return (keymap[50] or keymap[62]) * Keyboard.SHIFT_MOD + \
               (keymap[37]) * Keyboard.CTRL_MOD + \
               (keymap[64]) * Keyboard.ALT_MOD

    def press_key(self, key_name, modifier = 0):
        self.press_key(keycode_for_key_name(key_name), modifier)

    def press_key(self, keycode, modifier = 0):
        self._change_key(keycode, Keyboard.PRESS, modifier)

    def release_key(self, key_name, modifier = 0):
        self.release_key(keycode_for_key_name(key_name), modifier)

    def release_key(self, keycode, modifier = 0):
        self._change_key(keycode, Keyboard.RELEASE, modifier)

    def _change_key(self, keycode, direction, modifier=0):
        modifier = int(modifier)
        keycode = keycode + 8 # Convert linux keycodes to X11 ones
        root = self.display.screen().root

        if direction == Keyboard.PRESS:
            event = Xlib.protocol.event.KeyPress(
                    detail = keycode,
                    time = 0,
                    root = root,
                    window = self.focused_window,
                    child = Xlib.X.NONE,
                    root_x = 0,
                    root_y = 0,
                    event_x = 1,
                    event_y = 1,
                    state = modifier,
                    same_screen = 0)
        elif direction == Keyboard.RELEASE:
            event = Xlib.protocol.event.KeyRelease(
                    detail = keycode,
                    time = 0,
                    root = root,
                    window = self.focused_window,
                    child = Xlib.X.NONE,
                    root_x = 0,
                    root_y = 0,
                    event_x = 1,
                    event_y = 1,
                    state = modifier,
                    same_screen = 0)
        else:
            assert(False)

        self.display.send_event(self.focused_window, event, True, Xlib.X.KeyPress | Xlib.X.KeyRelease)
        self.display.flush()

window_owners = {}

def handle_error(*args):
    window_id = args[0].resource_id.id
    if window_id in window_owners:
        window_owners[window_id].window_closed(window_id);
    else:
        print("Orphan window closed:", window_id)

def suppress_error(*args):
    pass

class Harness(object):
    def __init__(self):
        window_count = x_tiles * y_tiles
        self.window_title = window_title
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
        self.captures = [image_capture.ImageCapture(x_res, y_res) for _ in range(window_count)]

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
        split_command = shlex.split(command)
        process = subprocess.Popen(split_command, cwd=directory, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        open_windows = Harness.GetAllWindowsWithName(self.window_title, self.root_window, [])
        for w in open_windows:
            if w not in self.windows:
                # Make sure we haven't opened too many instances
                assert(None in self.windows)
                loc = self.windows.index(None)
                self.windows[loc] = w
                self.keyboards[loc] = Keyboard(self.display, w)
                print(w)
                print(hex(w.id))
                subprocess.Popen(["i3-msg", "[id=" + hex(w.id) + "]", "floating", "enable;", \
                                                                      "border", "pixel", "0"])
                self.display.flush()
                time.sleep(1)
                self.display.flush()
                w.configure(x = x_res * (loc % x_tiles), y = y_res * (loc // x_tiles), width = x_res, height = y_res)
                self.display.flush()
                window_owners[w.id] = self

    # Unused?
    def tick(self):
        # Sleep here to enforce a max fps.
        tick_duration = 1/fps
        tick_end = time.time()
        elapsed = tick_end - self.tick_start
        sleep_length = tick_duration - elapsed

        print("tick")

        if sleep_length > 0:
            time.sleep(sleep_length)

        if None in self.windows:
            self.connect_to_windows()

        self.tick_start = time.time()

        while self.display.pending_events() > 0:
            print(self.display.next_event())

        if self.windows.count(-1) == len(self.windows):
            print("All windows closed. Exiting.")
            return False

        return True

    def get_screen(self, instance = 0):
        if self.windows[instance] is not None:
            im = self.captures[instance].get_image(self.windows[instance].id)
            return im[:, :, 2::-1]
        else:
            return np.zeros([y_res, x_res, 4], dtype='uint8')

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

    def setup_reward(self, reward_class):
        self.get_reward = reward_class.get_reward
