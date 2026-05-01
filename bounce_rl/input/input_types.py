"""Input action types."""

from dataclasses import dataclass
from enum import IntEnum
from typing import Union

# Type alias for key values
Keycode = int
MouseButton = int


class KeyActionKind(IntEnum):
    KEY_ACTION_NONE = 0
    KEY_PRESS = 1  # Press and release
    KEY_DOWN = 2  # Press and hold
    KEY_UP = 3  # Release


class MouseActionKind(IntEnum):
    NONE = 0
    BTN_PRESS = 1
    BTN_DOWN = 2
    BTN_UP = 3
    MOVE = 4
    DRAG = 5


class ButtonActionKind(IntEnum):
    NONE = 0
    PRESS = 1
    DOWN = 2
    UP = 3


class KeyDirection(IntEnum):
    KEY_NO_DIRECTION = 0
    KEY_DOWN = 1
    KEY_UP = 2


@dataclass(frozen=True)
class KeyAction:
    action: KeyActionKind
    keycode: Keycode

    @staticmethod
    def press(keycode: Keycode) -> "KeyAction":
        return KeyAction(action=KeyActionKind.KEY_PRESS, keycode=keycode)

    @staticmethod
    def down(keycode: Keycode) -> "KeyAction":
        return KeyAction(action=KeyActionKind.KEY_DOWN, keycode=keycode)

    @staticmethod
    def up(keycode: Keycode) -> "KeyAction":
        return KeyAction(action=KeyActionKind.KEY_UP, keycode=keycode)

    def get_button(self):
        return self.keycode


@dataclass(frozen=True)
class MouseButtonAction:
    action: MouseActionKind
    button: MouseButton

    @staticmethod
    def press(button: MouseButton) -> "MouseButtonAction":
        return MouseButtonAction(action=MouseActionKind.BTN_PRESS, button=button)

    @staticmethod
    def down(button: MouseButton) -> "MouseButtonAction":
        return MouseButtonAction(action=MouseActionKind.BTN_DOWN, button=button)

    @staticmethod
    def up(button: MouseButton) -> "MouseButtonAction":
        return MouseButtonAction(action=MouseActionKind.BTN_UP, button=button)

    def get_button(self):
        return self.button


@dataclass(frozen=True)
class MouseMoveAction:
    position: tuple[int, int]


@dataclass(frozen=True)
class MouseDragAction:
    start: tuple[int, int]
    end: tuple[int, int]
    button: MouseButton


@dataclass(frozen=True)
class ScrollAction:
    direction: KeyDirection


InputAction = Union[
    KeyAction,
    MouseMoveAction,
    MouseButtonAction,
    MouseDragAction,
    ScrollAction,
]
