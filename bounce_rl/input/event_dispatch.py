"""
Event dispatch for the BounceRL input system.

This module dispatches low-level input events to desktop backends.
"""

from typing import List

from bounce_rl.input.input_types import (
    InputAction,
    KeyAction,
    KeyActionKind,
    KeyDirection,
    MouseActionKind,
    MouseButtonAction,
    MouseDragAction,
    MouseMoveAction,
    ScrollAction,
)
from bounce_rl.input.keys import MouseButtons
from bounce_desktop import Desktop


def apply_events_to_desktop(events: List[InputAction], desktop) -> None:
    """Dispatch input events to a Desktop backend."""
    for event in events:
        if isinstance(event, MouseDragAction):
            raise ValueError(
                "apply_events_to_desktop should only receive raw event actions. "
                "Not compound actions like MouseDragAction."
            )
        if isinstance(event, KeyAction) and event.action == KeyActionKind.KEY_PRESS:
            raise ValueError(
                "apply_events_to_desktop should only receive raw event actions. "
                "Not compound actions like KeyActionKind.KEY_PRESS."
            )
        if (
            isinstance(event, MouseButtonAction)
            and event.action == MouseActionKind.BTN_PRESS
        ):
            raise ValueError(
                "apply_events_to_desktop should only receive raw event actions. "
                "Not compound actions like MouseActionKind.BTN_PRESS."
            )

        if isinstance(event, KeyAction):
            _dispatch_key_action(event, desktop)
        elif isinstance(event, MouseButtonAction):
            _dispatch_mouse_button_action(event, desktop)
        elif isinstance(event, MouseMoveAction):
            desktop.move_mouse_to(event.position[0], event.position[1])
        elif isinstance(event, ScrollAction):
            _dispatch_scroll_action(event, desktop)
        else:
            assert False


def _dispatch_key_action(event: KeyAction, desktop: Desktop) -> None:
    if event.keycode in MouseButtons:
        _dispatch_mouse_button_action(
            MouseButtonAction(
                action=_mouse_action_kind_from_key_action_kind(event.action),
                button=event.keycode,
            ),
            desktop,
        )
        return

    if event.action == KeyActionKind.KEY_DOWN:
        desktop.keycode_down(event.keycode)
    elif event.action == KeyActionKind.KEY_UP:
        desktop.keycode_up(event.keycode)
    else:
        assert False


def _dispatch_mouse_button_action(event: MouseButtonAction, desktop) -> None:
    if event.action == MouseActionKind.BTN_DOWN:
        desktop.mouse_press(event.button)
    elif event.action == MouseActionKind.BTN_UP:
        desktop.mouse_release(event.button)
    else:
        assert False


def _dispatch_scroll_action(event: ScrollAction, desktop) -> None:
    if hasattr(desktop, "scroll"):
        desktop.scroll(event.direction)
    elif event.direction == KeyDirection.KEY_DOWN and hasattr(desktop, "scroll_down"):
        desktop.scroll_down()
    elif event.direction == KeyDirection.KEY_UP and hasattr(desktop, "scroll_up"):
        desktop.scroll_up()


def _mouse_action_kind_from_key_action_kind(action: KeyActionKind) -> MouseActionKind:
    if action == KeyActionKind.KEY_DOWN:
        return MouseActionKind.BTN_DOWN
    if action == KeyActionKind.KEY_UP:
        return MouseActionKind.BTN_UP
    if action == KeyActionKind.KEY_PRESS:
        return MouseActionKind.BTN_PRESS
    return MouseActionKind.NONE
