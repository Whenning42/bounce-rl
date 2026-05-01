"""Tests for event_dispatch.py"""

import unittest

from bounce_rl.input.event_dispatch import apply_events_to_desktop
from bounce_rl.input.input_types import (
    KeyAction,
    KeyActionKind,
    KeyDirection,
    MouseActionKind,
    MouseButtonAction,
    MouseDragAction,
    MouseMoveAction,
    ScrollAction,
)
from bounce_rl.input.keys import BTN_LEFT, BTN_MIDDLE, BTN_RIGHT, KEY_A, KEY_B


class MockDesktop:
    """Mock desktop for testing event dispatch."""

    def __init__(self):
        self.events = []

    def key_press(self, keycode: int):
        self.events.append(("key_press", keycode))

    def key_release(self, keycode: int):
        self.events.append(("key_release", keycode))

    def move_mouse(self, x: int, y: int):
        self.events.append(("move_mouse", x, y))

    def mouse_press(self, button: int):
        self.events.append(("mouse_press", button))

    def mouse_release(self, button: int):
        self.events.append(("mouse_release", button))

    def scroll(self, direction: KeyDirection):
        self.events.append(("scroll", direction))


class TestEventDispatch(unittest.TestCase):
    """Tests for apply_events_to_desktop."""

    def test_key_events(self):
        """Key down/up actions invoke key_press/key_release with evdev keycodes."""
        desktop = MockDesktop()
        events = [
            KeyAction.down(KEY_A),
            KeyAction.up(KEY_B),
        ]

        apply_events_to_desktop(events, desktop)

        self.assertEqual(desktop.events, [("key_press", KEY_A), ("key_release", KEY_B)])

    def test_mouse_move_events(self):
        """Mouse move actions invoke move_mouse with coordinates passed through."""
        desktop = MockDesktop()
        events = [MouseMoveAction((100, 200)), MouseMoveAction((300, 400))]

        apply_events_to_desktop(events, desktop)

        self.assertEqual(
            desktop.events, [("move_mouse", 100, 200), ("move_mouse", 300, 400)]
        )

    def test_mouse_button_events(self):
        """Mouse button down/up actions pass evdev button codes through."""
        desktop = MockDesktop()
        events = [
            MouseButtonAction.up(BTN_LEFT),
            MouseButtonAction.down(BTN_RIGHT),
            MouseButtonAction.down(BTN_MIDDLE),
        ]

        apply_events_to_desktop(events, desktop)

        self.assertEqual(
            desktop.events,
            [
                ("mouse_release", BTN_LEFT),
                ("mouse_press", BTN_RIGHT),
                ("mouse_press", BTN_MIDDLE),
            ],
        )

    def test_mouse_button_key_actions_are_dispatched_as_mouse_events(self):
        """Mouse button key actions are routed to mouse_press/mouse_release."""
        desktop = MockDesktop()
        events = [
            KeyAction.down(BTN_LEFT),
            KeyAction.up(BTN_LEFT),
        ]

        apply_events_to_desktop(events, desktop)

        self.assertEqual(
            desktop.events,
            [("mouse_press", BTN_LEFT), ("mouse_release", BTN_LEFT)],
        )

    def test_scroll_action(self):
        """Scroll actions are passed to desktop.scroll when available."""
        desktop = MockDesktop()

        apply_events_to_desktop([ScrollAction(KeyDirection.KEY_DOWN)], desktop)

        self.assertEqual(desktop.events, [("scroll", KeyDirection.KEY_DOWN)])

    def test_rejects_compound_actions(self):
        """Compound actions must be split before dispatch."""
        desktop = MockDesktop()
        compound_actions = [
            KeyAction.press(KEY_A),
            MouseButtonAction.press(BTN_LEFT),
            MouseDragAction((0, 0), (1, 1), BTN_LEFT),
        ]

        for action in compound_actions:
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    apply_events_to_desktop([action], desktop)

    def test_mixed_raw_events(self):
        """Mixed raw key, mouse, and pointer actions dispatch in order."""
        desktop = MockDesktop()
        events = [
            KeyAction.down(KEY_A),
            MouseMoveAction((50, 75)),
            MouseButtonAction.down(BTN_LEFT),
            KeyAction.up(KEY_A),
            MouseButtonAction.up(BTN_LEFT),
        ]

        apply_events_to_desktop(events, desktop)

        self.assertEqual(
            desktop.events,
            [
                ("key_press", KEY_A),
                ("move_mouse", 50, 75),
                ("mouse_press", BTN_LEFT),
                ("key_release", KEY_A),
                ("mouse_release", BTN_LEFT),
            ],
        )


if __name__ == "__main__":
    unittest.main()
