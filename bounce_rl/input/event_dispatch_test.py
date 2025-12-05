"""Tests for event_dispatch.py"""

import unittest

from bounce_rl.input.event_dispatch import apply_bounce_desktop_events
from bounce_rl.input.input_types import KeyDirection, KeyEvent, MouseEvent
from bounce_rl.input.keys import (
    KEY_A,
    KEY_B,
    LEFT_MOUSE_BUTTON,
    MIDDLE_MOUSE_BUTTON,
    RIGHT_MOUSE_BUTTON,
)


class MockDesktop:
    """Mock desktop for testing event dispatch."""

    def __init__(self):
        self.events = []

    def key_press(self, keysym: int):
        self.events.append(("key_press", keysym))

    def key_release(self, keysym: int):
        self.events.append(("key_release", keysym))

    def move_mouse(self, x: int, y: int):
        self.events.append(("move_mouse", x, y))

    def mouse_press(self, button: int):
        self.events.append(("mouse_press", button))

    def mouse_release(self, button: int):
        self.events.append(("mouse_release", button))


class TestEventDispatch(unittest.TestCase):
    """Tests for apply_bounce_desktop_events."""

    def test_key_events(self):
        """KeyUp and KeyDown events invoke key_press and key_release with keysym passed
        through."""
        desktop = MockDesktop()
        events = [
            KeyEvent(action=KeyDirection.KEY_DOWN, key=KEY_A),
            KeyEvent(action=KeyDirection.KEY_UP, key=KEY_B),
        ]

        apply_bounce_desktop_events(events, desktop)

        self.assertEqual(desktop.events, [("key_press", KEY_A), ("key_release", KEY_B)])

    def test_mouse_move_events(self):
        """Move mouse event invokes move_mouse with correct x and y passed through."""
        desktop = MockDesktop()
        events = [MouseEvent(position=(100, 200)), MouseEvent(position=(300, 400))]

        apply_bounce_desktop_events(events, desktop)

        self.assertEqual(
            desktop.events, [("move_mouse", 100, 200), ("move_mouse", 300, 400)]
        )

    def test_pointer_button_events(self):
        """Pointer button events invoke mouse_press/mouse_release."""
        desktop = MockDesktop()
        events = [
            KeyEvent(action=KeyDirection.KEY_UP, key=LEFT_MOUSE_BUTTON),
            KeyEvent(action=KeyDirection.KEY_DOWN, key=RIGHT_MOUSE_BUTTON),
            KeyEvent(action=KeyDirection.KEY_DOWN, key=MIDDLE_MOUSE_BUTTON),
        ]

        apply_bounce_desktop_events(events, desktop)

        self.assertEqual(
            desktop.events,
            [("mouse_release", 1), ("mouse_press", 2), ("mouse_press", 3)],
        )

    def test_mixed_events(self):
        """Mixed key, mouse, and pointer events are dispatched correctly."""
        desktop = MockDesktop()
        events = [
            KeyEvent(action=KeyDirection.KEY_DOWN, key=KEY_A),
            MouseEvent(position=(50, 75)),
            KeyEvent(action=KeyDirection.KEY_DOWN, key=LEFT_MOUSE_BUTTON),
            KeyEvent(action=KeyDirection.KEY_UP, key=KEY_A),
            KeyEvent(action=KeyDirection.KEY_UP, key=LEFT_MOUSE_BUTTON),
        ]

        apply_bounce_desktop_events(events, desktop)

        self.assertEqual(
            desktop.events,
            [
                ("key_press", KEY_A),
                ("move_mouse", 50, 75),
                ("mouse_press", 1),
                ("key_release", KEY_A),
                ("mouse_release", 1),
            ],
        )


if __name__ == "__main__":
    unittest.main()
