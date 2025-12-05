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
    KEY_DOWN = 2   # Press and hold
    KEY_UP = 3     # Release


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


@dataclass(frozen=True)
class KeyEvent:
    """
    A raw key event sent to the desktop.

    Represents a single key press or release event.
    """
    action: KeyDirection
    key: Key


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


@dataclass(frozen=True)
class MouseEvent:
    """
    A raw mouse move event sent to the desktop.

    All mouse events use absolute screen pixel positions.
    """
    position: tuple[int, int]


# Union types for input actions and events
InputAction = Union[KeyAction, MouseAction]
InputEvent = Union[KeyEvent, MouseEvent]


# Factory functions for creating MouseActions

def move_mouse(delta_position: tuple[int, int]) -> MouseAction:
    """Create a relative mouse move action."""
    return MouseAction(
        is_relative=True,
        position=delta_position,
        is_drag=False,
        drag_button=None
    )


def move_to(position: tuple[int, int]) -> MouseAction:
    """Create an absolute mouse move action."""
    return MouseAction(
        is_relative=False,
        position=position,
        is_drag=False,
        drag_button=None
    )


def drag_mouse(button: Key, delta_position: tuple[int, int]) -> MouseAction:
    """Create a relative mouse drag action."""
    return MouseAction(
        is_relative=True,
        position=delta_position,
        is_drag=True,
        drag_button=button
    )


def drag_mouse_to(button: Key, position: tuple[int, int]) -> MouseAction:
    """Create an absolute mouse drag action."""
    return MouseAction(
        is_relative=False,
        position=position,
        is_drag=True,
        drag_button=button
    )
