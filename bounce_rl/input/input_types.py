"""
Input action and event types for the BounceRL input system.

This module defines the data structures for representing input actions and events.
Actions are higher-level PyAutoGUI-style inputs, while events are raw low-level
inputs sent to the desktop backend.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Union

# Type alias for key values
Key = int


class KeyActionType(IntEnum):
    """High-level key action types."""

    KEY_PRESS = 1  # Press and release
    KEY_DOWN = 2  # Press and hold
    KEY_UP = 3  # Release


class KeyDirection(IntEnum):
    """Low-level key event directions."""

    KEY_DOWN = 0
    KEY_UP = 1


@dataclass(frozen=True)
class KeyAction:
    """
    A high-level key action (PyAutoGUI-style).

    Can represent pressing a key (down then up), holding a key down,
    or releasing a held key.
    """

    action: KeyActionType
    key: Key


def key_press_action(key: Key) -> KeyAction:
    return KeyAction(action=KeyActionType.KEY_PRESS, key=key)


def key_down_action(key: Key) -> KeyAction:
    return KeyAction(action=KeyActionType.KEY_DOWN, key=key)


def key_up_action(key: Key) -> KeyAction:
    return KeyAction(action=KeyActionType.KEY_UP, key=key)


@dataclass(frozen=True)
class KeyEvent:
    """
    A raw key event sent to the desktop.

    Represents a single key press or release event.
    """

    action: KeyDirection
    keysym: Key


def key_down_event(keysym: Key) -> KeyEvent:
    return KeyEvent(action=KeyDirection.KEY_DOWN, keysym=keysym)


def key_up_event(keysym: Key) -> KeyEvent:
    return KeyEvent(action=KeyDirection.KEY_UP, keysym=keysym)


@dataclass(frozen=True)
class MouseAction:
    """
    A high-level mouse action.

    Can represent relative or absolute mouse moves, as well as drag operations.
    Mouse coordinates are in screen pixels.
    """

    is_relative: bool
    position: tuple[int, int]
    is_drag: bool
    drag_button: Key | None


def move_mouse_action(delta_position: tuple[int, int]) -> MouseAction:
    return MouseAction(
        is_relative=True, position=delta_position, is_drag=False, drag_button=None
    )


def move_to_action(position: tuple[int, int]) -> MouseAction:
    return MouseAction(
        is_relative=False, position=position, is_drag=False, drag_button=None
    )


def drag_mouse_action(button: Key, delta_position: tuple[int, int]) -> MouseAction:
    return MouseAction(
        is_relative=True, position=delta_position, is_drag=True, drag_button=button
    )


def drag_mouse_to_action(button: Key, position: tuple[int, int]) -> MouseAction:
    return MouseAction(
        is_relative=False, position=position, is_drag=True, drag_button=button
    )


@dataclass(frozen=True)
class MouseEvent:
    """
    A raw mouse move event sent to the desktop.

    All mouse events use absolute screen pixel positions.
    """

    position: tuple[int, int]


def mouse_move_event(position: tuple[int, int]) -> MouseEvent:
    return MouseEvent(position=position)


InputAction = Union[KeyAction, MouseAction]
InputEvent = Union[KeyEvent, MouseEvent]
