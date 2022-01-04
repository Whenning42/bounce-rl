from Xlib import display
import Xlib.X
import Xlib.XK
import Xlib.protocol
import numpy as np

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
            # Unsupported direction
            assert(False)

        self.display.send_event(self.focused_window, event, True, Xlib.X.KeyPress | Xlib.X.KeyRelease)
        self.display.flush()
