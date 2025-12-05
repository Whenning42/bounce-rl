"""
Event dispatch for the BounceRL input system.

This module dispatches low-level input events to desktop backends.
"""

from typing import List

from bounce_rl.input.input_types import InputEvent, KeyDirection, KeyEvent, MouseEvent


def apply_bounce_desktop_events(events: List[InputEvent], desktop) -> None:
    """
    Dispatch input events to a Desktop backend.

    Invokes the appropriate event handlers on the desktop object based on
    the event type.

    Args:
        events: List of input events to dispatch
        desktop: Desktop backend object with event handler methods:
            - key_press(keysym: int) - Called for key down events
            - key_release(keysym: int) - Called for key up events
            - move_mouse(x: int, y: int) - Called for mouse move events
            - mouse_press(button: int) - Called for mouse button down events
            - mouse_release(button: int) - Called for mouse button up events
    """
    for event in events:
        if isinstance(event, KeyEvent):
            # Check if this is a mouse button (pointer buttons use KeyEvent)
            if _is_pointer_button(event.key):
                button = _keysym_to_button_number(event.key)
                if event.action == KeyDirection.KEY_DOWN:
                    desktop.mouse_press(button)
                else:  # KEY_UP
                    desktop.mouse_release(button)
            else:
                # Regular keyboard key
                if event.action == KeyDirection.KEY_DOWN:
                    desktop.key_press(event.key)
                else:  # KEY_UP
                    desktop.key_release(event.key)
        elif isinstance(event, MouseEvent):
            desktop.move_mouse(event.position[0], event.position[1])


def _is_pointer_button(keysym: int) -> bool:
    """Check if a keysym represents a pointer button."""
    # Pointer buttons are in the range 0xFEE9-0xFEED
    return 0xFEE9 <= keysym <= 0xFEED


def _keysym_to_button_number(keysym: int) -> int:
    """Convert pointer button keysym to button number (1-5)."""
    # KEY_POINTER_BUTTON1 = 0xFEE9 -> button 1
    # KEY_POINTER_BUTTON2 = 0xFEEA -> button 2
    # etc.
    return keysym - 0xFEE9 + 1
