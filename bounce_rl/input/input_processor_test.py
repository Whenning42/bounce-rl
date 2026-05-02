"""Tests for input_processor.py"""

import unittest

from bounce_rl.input.input_processor import InputProcessor
from bounce_rl.input.input_types import (
    KeyAction,
    MouseButtonAction,
    MouseDragAction,
    MouseMoveAction,
)
from bounce_rl.input.keys import BTN_LEFT, KEY_A, KEY_B, KEY_C, KEY_D


class TestButtonStateHandling(unittest.TestCase):
    """Tests for key and mouse button state handling."""

    def test_key_down_and_up_are_raw_events(self):
        """Key down/up actions pass through as raw down/up actions."""
        processor = InputProcessor(800, 600)
        actions = [
            KeyAction.down(KEY_A),
            KeyAction.up(KEY_A),
        ]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(immediate, actions)
        self.assertEqual(delayed, [])

    def test_key_press_returns_immediate_and_delayed_events(self):
        """Key press actions split into immediate down and delayed up."""
        processor = InputProcessor(800, 600)

        immediate, delayed = processor.process_input_actions([KeyAction.press(KEY_A)])

        self.assertEqual(immediate, [KeyAction.down(KEY_A)])
        self.assertEqual(delayed, [KeyAction.up(KEY_A)])

    def test_mouse_button_press_returns_immediate_and_delayed_events(self):
        """Mouse button press actions split into immediate down and delayed up."""
        processor = InputProcessor(800, 600)

        immediate, delayed = processor.process_input_actions(
            [MouseButtonAction.press(BTN_LEFT)]
        )

        self.assertEqual(immediate, [MouseButtonAction.down(BTN_LEFT)])
        self.assertEqual(delayed, [MouseButtonAction.up(BTN_LEFT)])

    def test_mouse_move_passes_through(self):
        """Mouse move actions are already raw events."""
        processor = InputProcessor(800, 600)
        action = MouseMoveAction((10, 20))

        immediate, delayed = processor.process_input_actions([action])

        self.assertEqual(immediate, [action])
        self.assertEqual(delayed, [])

    def test_mouse_drag_returns_immediate_and_delayed_events(self):
        """Mouse drag actions split into raw move/down/move/up events."""
        processor = InputProcessor(800, 600)
        action = MouseDragAction((0, 0), (10, 20), BTN_LEFT)

        immediate, delayed = processor.process_input_actions([action])

        self.assertEqual(
            immediate,
            [
                MouseMoveAction((0, 0)),
                MouseButtonAction.down(BTN_LEFT),
                MouseMoveAction((10, 20)),
            ],
        )
        self.assertEqual(delayed, [MouseButtonAction.up(BTN_LEFT)])


class TestReleaseButtons(unittest.TestCase):
    """Tests for release_buttons()."""

    def test_release_buttons_releases_held_keys(self):
        """release_buttons returns key-up actions for currently held keys."""
        processor = InputProcessor(800, 600)
        actions = [
            KeyAction.down(KEY_B),
            KeyAction.down(KEY_C),
            KeyAction.down(KEY_D),
            KeyAction.up(KEY_D),
        ]

        processor.process_input_actions(actions)
        result = processor.release_buttons()

        self.assertEqual(set(result), {KeyAction.up(KEY_B), KeyAction.up(KEY_C)})

    def test_release_buttons_releases_held_mouse_buttons(self):
        """release_buttons returns mouse-button-up actions for held mouse buttons."""
        processor = InputProcessor(800, 600)

        processor.process_input_actions([MouseButtonAction.down(BTN_LEFT)])
        result = processor.release_buttons()

        self.assertEqual(result, [MouseButtonAction.up(BTN_LEFT)])


if __name__ == "__main__":
    unittest.main()
