"""
Evdev key and button code definitions for the BounceRL input system.

Values mirror Linux input-event-codes.h. These are physical key/button codes,
so shifted symbols like "!" or "@" are represented by their digit key plus a
separate shift action instead of by a separate keysym.
"""

Keycode = int
Button = int

# Letters
KEY_Q = 16
KEY_W = 17
KEY_E = 18
KEY_R = 19
KEY_T = 20
KEY_Y = 21
KEY_U = 22
KEY_I = 23
KEY_O = 24
KEY_P = 25
KEY_A = 30
KEY_S = 31
KEY_D = 32
KEY_F = 33
KEY_G = 34
KEY_H = 35
KEY_J = 36
KEY_K = 37
KEY_L = 38
KEY_Z = 44
KEY_X = 45
KEY_C = 46
KEY_V = 47
KEY_B = 48
KEY_N = 49
KEY_M = 50

# Number row
KEY_1 = 2
KEY_2 = 3
KEY_3 = 4
KEY_4 = 5
KEY_5 = 6
KEY_6 = 7
KEY_7 = 8
KEY_8 = 9
KEY_9 = 10
KEY_0 = 11

# Symbol keys
KEY_MINUS = 12
KEY_EQUAL = 13
KEY_LEFTBRACE = 26
KEY_RIGHTBRACE = 27
KEY_BACKSLASH = 43
KEY_SEMICOLON = 39
KEY_APOSTROPHE = 40
KEY_GRAVE = 41
KEY_COMMA = 51
KEY_DOT = 52
KEY_SLASH = 53

# Existing repo-facing aliases for symbol key positions.
KEY_BRACKETLEFT = KEY_LEFTBRACE
KEY_BRACKETRIGHT = KEY_RIGHTBRACE
KEY_PERIOD = KEY_DOT

# Function keys
KEY_F1 = 59
KEY_F2 = 60
KEY_F3 = 61
KEY_F4 = 62
KEY_F5 = 63
KEY_F6 = 64
KEY_F7 = 65
KEY_F8 = 66
KEY_F9 = 67
KEY_F10 = 68
KEY_F11 = 87
KEY_F12 = 88

# Modifiers
KEY_LEFTCTRL = 29
KEY_LEFTSHIFT = 42
KEY_LEFTALT = 56

# Existing repo-facing modifier aliases.
KEY_CONTROL_L = KEY_LEFTCTRL
KEY_SHIFT_L = KEY_LEFTSHIFT
KEY_ALT_L = KEY_LEFTALT

# Other keys
KEY_ESC = 1
KEY_BACKSPACE = 14
KEY_TAB = 15
KEY_ENTER = 28
KEY_SPACE = 57

# Existing repo-facing aliases.
KEY_ESCAPE = KEY_ESC

# Pointer buttons
BTN_LEFT = 1
BTN_RIGHT = 2
BTN_MIDDLE = 3

# Existing repo-facing mouse aliases.
LEFT_MOUSE_BUTTON = BTN_LEFT
RIGHT_MOUSE_BUTTON = BTN_RIGHT
MIDDLE_MOUSE_BUTTON = BTN_MIDDLE

# Key classes - sets of related evdev codes.
Letters = (
    KEY_A,
    KEY_B,
    KEY_C,
    KEY_D,
    KEY_E,
    KEY_F,
    KEY_G,
    KEY_H,
    KEY_I,
    KEY_J,
    KEY_K,
    KEY_L,
    KEY_M,
    KEY_N,
    KEY_O,
    KEY_P,
    KEY_Q,
    KEY_R,
    KEY_S,
    KEY_T,
    KEY_U,
    KEY_V,
    KEY_W,
    KEY_X,
    KEY_Y,
    KEY_Z,
)

Symbols = (
    KEY_0,
    KEY_1,
    KEY_2,
    KEY_3,
    KEY_4,
    KEY_5,
    KEY_6,
    KEY_7,
    KEY_8,
    KEY_9,
    KEY_MINUS,
    KEY_EQUAL,
    KEY_LEFTBRACE,
    KEY_RIGHTBRACE,
    KEY_BACKSLASH,
    KEY_SEMICOLON,
    KEY_APOSTROPHE,
    KEY_GRAVE,
    KEY_COMMA,
    KEY_DOT,
    KEY_SLASH,
)

FnKeys = (
    KEY_F1,
    KEY_F2,
    KEY_F3,
    KEY_F4,
    KEY_F5,
    KEY_F6,
    KEY_F7,
    KEY_F8,
    KEY_F9,
    KEY_F10,
    KEY_F11,
    KEY_F12,
)

Modifiers = (KEY_SHIFT_L, KEY_ALT_L, KEY_CONTROL_L)

Other = (KEY_TAB, KEY_ESCAPE, KEY_ENTER, KEY_BACKSPACE, KEY_SPACE)

MouseButtons = (BTN_LEFT, BTN_RIGHT, BTN_MIDDLE)

AllKeys = Letters + Symbols + FnKeys + Modifiers + Other
