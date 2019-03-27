import atexit
import image_capture
import numpy as np
import os
import subprocess
import signal
import time
from model import *

from Xlib import display
import Xlib.X
import Xlib.XK
import Xlib.protocol

game_directory = "/home/william/.local/share/Steam/steamapps/common/Sky Rogue"
executable = "./skyrogue.x86"
binary_name = "skyrogue.x86"

fps = 24
x_res = 640
y_res = 480
x_tiles = 1
y_tiles = 1

# harness interface
#   tick() returns True if the underlying game is still running
#   get_screen() returns a bitmap of the game's full window
#   perform_actions(keymap) uses the provided keymap
#   reset_handler() hardcoded implementation to handle game launch and resets ?
#     This might not be necessary if curiosity implementation works out

# We need to figure out keymap formats. Models will output 1 hot vectors and eventually, those need to get turned into keycodes or scancodes or something.

def GetAllWindowsWithName(name, parent, matches):
    for child in parent.query_tree().children:
        if child.get_wm_name() is not None:
            print("Child: " + child.get_wm_name())
        if child.get_wm_name() == name:
            matches.append(child)
        matches = GetAllWindowsWithName(name, child, matches)
    return matches

def KillRunningPrograms():
    ps = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = ps.communicate()
    for p in out.decode('ascii').splitlines():
        if binary_name in p:
            pid = int(p.split()[0])
            os.kill(pid, signal.SIGKILL)

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

class Harness(object):
    def __init__(self):
        instances = x_tiles * y_tiles
        self.tick_start = time.time()
        self.display = display.Display()
        self.root_window = self.display.screen().root
        #self.keyboards = [Keyboard(None)]
        #return
        for i in range(instances):
            # Skyrogue tries launching steam if the working directory
            # isn't the game's directory.
            subprocess.Popen([executable], cwd=game_directory, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        atexit.register(KillRunningPrograms)
        self.windows = self.connect_to_windows("Sky Rogue", instances)
        self.keyboards = []
        for w in range(instances):
            self.windows[w].configure(x = x_res*(w%x_tiles), y = y_res*(w//x_tiles))
            self.keyboards.append(Keyboard(self.display, self.windows[w]))
        self.window_x = self.windows[0].get_geometry().width
        self.window_y = self.windows[0].get_geometry().height
        print("Dimensions: " + str(self.window_x) + ", " + str(self.window_y))
        self.capture = image_capture.ImageCapture(self.window_x, self.window_y)
        #self._focus_windows()
        #self._disable_user_input()

    def connect_to_windows(self, title, count):
        time.sleep(3)
        windows = GetAllWindowsWithName("Sky Rogue", self.root_window, [])
        print("Found " + str(len(windows)) + " windows")
        if len(windows) != count:
            print("Failed trying to capture windows")
            assert(False)
        return windows

    def tick(self):
        # Sleep here to enforce a max fps.
        tick_duration = 1/fps
        tick_end = time.time()
        elapsed = tick_end - self.tick_start
        sleep_length = tick_duration - elapsed

        if sleep_length > 0:
            time.sleep(sleep_length)

        self.tick_start = time.time()
        return True

    def get_screen(self):
        return self.capture.get_image(self.windows[0].id)

    def _focus_windows(self):
        for w in self.windows:
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
        #self._focus_windows()
        #self._disable_user_input()
        #for w in self.windows:
        #    self.capture.FocusAndIgnoreAllEvents(w.id)
        for keyboard in self.keyboards:
            keyboard.set_keymap(keymap)
