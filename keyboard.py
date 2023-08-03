# Implements a virtual X11 keyboard.

from Xlib import display
from Xlib.ext import xtest
import Xlib.X
import Xlib.XK
import Xlib.protocol
import numpy as np
import time
from enum import Enum

from threading import Lock

def keysym_for_key_name(key_name):
    keysym = Xlib.XK.string_to_keysym(key_name)
    assert(keysym is not None)
    return keysym

class KeyboardEventMode(Enum):
    SEND_EVENT = 1
    FAKE_INPUT = 2

class Keyboard(object):
    PRESS = 1
    RELEASE = -1
    SHIFT_MOD = 1
    CTRL_MOD = 4
    ALT_MOD = 8

    global_mutex = Lock()

    def __init__(self, display, window, keyboard_config):
        self.last_keymap = np.zeros(84)
        self.focused_window = window
        print("Keyboard win:", window)
        self.display = display
        self.sequence_keydown_time = keyboard_config.get("sequence_keydown_time", .25)
        event_mode_req: str = keyboard_config.get("mode", "SEND_EVENT")
        self.event_mode: KeyboardEventMode = KeyboardEventMode[event_mode_req]

        self.held_set = set()

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

    # Takes a set of key names to be held down and performs the key presses and releases
    # that get the keyboard to that state.
    # Key set is provdided in the form of a set of x key names with the XK_ prefix removed.
    # Note: This function is oblivious to key presses and releases that occur from
    # any other method of this class and so calling this and other methods may be
    # error prone.
    def set_held_keys(self, key_set):
        # Implements re-press key mode.
        for key in self.held_set:
            self.release_key(key)
        time.sleep(.01)
        for key in key_set:
            self.press_key(key)
        self.held_set = key_set

        # Implements delta key mode.
        # pressed = set()
        # released = set()

        # for key in key_set:
        #     if key not in self.held_set:
        #         pressed.add(key)
        # for key in self.held_set:
        #     if key not in key_set:
        #         released.add(key)
        # for key in pressed:
        #     self.press_key(key)
        # for key in released:
        #     self.release_key(key)
        # self.held_set = key_set

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
        self._press_key(key_name, modifier)

    def _press_key(self, key_name, modifier = 0):
        print("Press:", key_name)
        self._change_key(key_name, Keyboard.PRESS, modifier)

    def release_key(self, key_name, modifier = 0):
        self._release_key(key_name, modifier)

    def _release_key(self, key_name, modifier = 0):
        self._change_key(key_name, Keyboard.RELEASE, modifier)

    def key_sequence(self, keys):
        for key in keys:
            time.sleep(.1)
            self.press_key(key)
            time.sleep(self.sequence_keydown_time)
            self.release_key(key)
            time.sleep(.25)

    def _get_key_x_event(self, key_name, direction, modifier = 0):
        keysym = keysym_for_key_name(key_name)
        keycode = self.display.keysym_to_keycode(keysym)

        modifier = int(modifier)
        root = self.display.screen().root

        if direction == Keyboard.PRESS:
            return Xlib.protocol.event.KeyPress(
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
            return Xlib.protocol.event.KeyRelease(
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
            # Unsupported direction
            assert(False)

    def _change_key(self, key_name, direction, modifier = 0):
        self.global_mutex.acquire()
        if self.event_mode == KeyboardEventMode.SEND_EVENT:
            # Focus the window we're sending the event to.
            for detail in [Xlib.X.NotifyAncestor, Xlib.X.NotifyVirtual, Xlib.X.NotifyInferior, Xlib.X.NotifyNonlinear, Xlib.X.NotifyNonlinearVirtual, Xlib.X.NotifyPointer, Xlib.X.NotifyPointerRoot, Xlib.X.NotifyDetailNone]:
                w = self.focused_window
                e = Xlib.protocol.event.FocusIn(display=self.display, window=w, detail=detail, mode=Xlib.X.NotifyNormal)
                self.display.send_event(w, e)
                self.display.flush()


            # Set the input focus to the window we want.
            self.display.set_input_focus(self.focused_window, Xlib.X.RevertToNone, Xlib.X.CurrentTime)

            event = self._get_key_x_event(key_name, direction, modifier)
            self.display.send_event(self.focused_window, event, propagate = False, event_mask = Xlib.X.KeyPress | Xlib.X.KeyRelease)
            # self.display.send_event(self.focused_window, event, propagate = False, event_mask = 0)
            self.display.flush()

            # self.display.sync()
        elif self.event_mode == KeyboardEventMode.FAKE_INPUT:
            keysym = keysym_for_key_name(key_name)
            keycode = self.display.keysym_to_keycode(keysym)

            if direction == Keyboard.PRESS:
                event_type = Xlib.X.KeyPress
            else:
                event_type = Xlib.X.KeyRelease

            # TODO: Make compatible with mouse controller.
            xtest.fake_input(self.display, Xlib.X.MotionNotify, x=500, y=500)
            xtest.fake_input(self.display, event_type, keycode)
            self.display.flush()
        self.global_mutex.release()
