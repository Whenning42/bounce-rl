from Xlib import display
import Xlib.X
import Xlib.XK
import Xlib.protocol
import numpy as np
import time

def keysym_for_key_name(key_name):
    keysym = Xlib.XK.string_to_keysym(key_name)
    assert(keysym is not None)
    return keysym

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
    # This function is oblivious to key presses and releases that occur from
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
        keysym = keysym_for_key_name(key_name)
        self._press_key(keysym, modifier)

    def _press_key(self, keysym, modifier = 0):
        self._change_key(keysym, Keyboard.PRESS, modifier)

    def release_key(self, key_name, modifier = 0):
        keysym = keysym_for_key_name(key_name)
        self._release_key(keysym, modifier)

    def _release_key(self, keysym, modifier = 0):
        self._change_key(keysym, Keyboard.RELEASE, modifier)

    def key_sequence(self, keys):
        for key in keys:
            time.sleep(.1)
            self.press_key(key)
            time.sleep(.25)
            self.release_key(key)
            time.sleep(.25)

    def _change_key(self, keysym, direction, modifier=0):
        modifier = int(modifier)
        keycode = self.display.keysym_to_keycode(keysym)
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
            # Unsupported direction
            assert(False)

        # Focus the window we're sending the event to.
        for detail in [Xlib.X.NotifyAncestor, Xlib.X.NotifyVirtual, Xlib.X.NotifyInferior, Xlib.X.NotifyNonlinear, Xlib.X.NotifyNonlinearVirtual, Xlib.X.NotifyPointer, Xlib.X.NotifyPointerRoot, Xlib.X.NotifyDetailNone]:
            w = self.focused_window
            e = Xlib.protocol.event.FocusIn(display=self.display, window=w, detail=detail, mode=Xlib.X.NotifyNormal)
            self.display.send_event(w, e)
            self.display.flush()

        self.display.send_event(self.focused_window, event, False, Xlib.X.KeyPress | Xlib.X.KeyRelease)
        self.display.flush()
