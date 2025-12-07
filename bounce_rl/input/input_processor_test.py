"""Tests for input_processor.py"""

import unittest

from bounce_rl.input.input_processor import InputProcessor
from bounce_rl.input.input_types import (
    KeyDirection,
    drag_mouse_action,
    key_down_action,
    key_down_event,
    key_press_action,
    key_up_action,
    key_up_event,
    mouse_move_event,
    move_mouse_action,
    move_to_action,
)
from bounce_rl.input.keys import (
    KEY_A,
    KEY_B,
    KEY_C,
    KEY_D,
    KEY_SHIFT_L,
    KEY_a,
    KEY_b,
    KEY_c,
    KEY_d,
)


class TestShiftCasing(unittest.TestCase):
    """Tests for shift key casing logic."""

    def test_shift_before_letter_gives_uppercase(self):
        """Holding shift before a letter press gives an upper case letter press."""
        processor = InputProcessor(800, 600)
        actions = [
            key_down_action(KEY_SHIFT_L),
            key_down_action(KEY_A),
        ]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(
            immediate,
            [
                key_down_event(KEY_SHIFT_L),
                key_down_event(KEY_A),
            ],
        )
        self.assertEqual(delayed, [])

    def test_shift_after_letter_gives_lowercase(self):
        """Holding shift after a letter press gives a lower case letter press."""
        processor = InputProcessor(800, 600)
        actions = [
            key_down_action(KEY_A),
            key_down_action(KEY_SHIFT_L),
        ]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(
            immediate,
            [
                key_down_event(KEY_a),
                key_down_event(KEY_SHIFT_L),
            ],
        )
        self.assertEqual(delayed, [])

    def test_release_uses_original_case(self):
        """Releasing a held key releases the key's original case."""
        processor = InputProcessor(800, 600)
        actions = [
            key_down_action(KEY_SHIFT_L),
            key_down_action(KEY_A),
            key_up_action(KEY_SHIFT_L),
            key_up_action(KEY_A),
        ]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(
            immediate,
            [
                key_down_event(KEY_SHIFT_L),
                key_down_event(KEY_A),
                key_up_event(KEY_SHIFT_L),
                # Expect that the released 'A' is uppercase even though shift has been
                # released.
                key_up_event(KEY_A),
            ],
        )
        self.assertEqual(delayed, [])


class TestKeyStateHandling(unittest.TestCase):
    """Tests for key up/down state handling."""

    def test_pressing_held_key_releases_key_first(self):
        """Pressing a held key generates a key-up before the press."""
        processor = InputProcessor(800, 600)
        actions = [
            key_down_action(KEY_A),
            key_press_action(KEY_A),
        ]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(
            immediate,
            [
                key_down_event(KEY_a),
                key_up_event(KEY_a),
                key_down_event(KEY_a),
            ],
        )
        self.assertEqual(
            delayed,
            [key_up_event(KEY_a)],
        )

    def test_releasing_up_key_generates_nothing(self):
        """Releasing an already up key generates nothing."""
        processor = InputProcessor(800, 600)
        actions = [key_up_action(KEY_A)]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(immediate, [])
        self.assertEqual(delayed, [])

    def test_pressing_down_pressed_key_generates_nothing(self):
        """Pressing down a pressed key generates nothing."""
        processor = InputProcessor(800, 600)
        actions = [
            key_down_action(KEY_A),
            key_down_action(KEY_A),
        ]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(
            immediate,
            [
                key_down_event(KEY_a),
            ],
        )
        self.assertEqual(delayed, [])


class TestDelayedEventsReturn(unittest.TestCase):
    """Tests for the two-list return mechanism."""

    def test_key_press_returns_immediate_and_delayed_events(self):
        """Verify that press actions correctly split into immediate down and delayed up."""
        processor = InputProcessor(800, 600)
        actions = [key_press_action(KEY_A)]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(
            immediate,
            [key_down_event(KEY_a)],
        )
        self.assertEqual(
            delayed,
            [key_up_event(KEY_a)],
        )

    def test_mouse_drag_returns_immediate_and_delayed_events(self):
        """Verify that drag actions correctly split events."""
        from bounce_rl.input.keys import LEFT_MOUSE_BUTTON

        processor = InputProcessor(800, 600)
        actions = [drag_mouse_action(LEFT_MOUSE_BUTTON, (10, 10))]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(
            immediate,
            [
                key_down_event(LEFT_MOUSE_BUTTON),
                mouse_move_event((10, 10)),
            ],
        )
        self.assertEqual(delayed, [key_up_event(LEFT_MOUSE_BUTTON)])


class TestReleaseButtons(unittest.TestCase):
    """Tests for release_buttons()."""

    def test_release_buttons_releases_held_keys(self):
        """Release buttons releases down buttons."""
        processor = InputProcessor(800, 600)
        actions = [
            key_press_action(KEY_A),
            key_down_action(KEY_B),
            key_down_action(KEY_C),
            key_down_action(KEY_D),
            key_up_action(KEY_D),
        ]

        processor.process_input_actions(actions)
        result = processor.release_buttons()

        # Should release B and C (A was pressed so it's not held, D was released)
        # Order may vary based on dict iteration
        self.assertEqual(set(result), set([key_up_event(KEY_b), key_up_event(KEY_c)]))


class TestMouseStateHandling(unittest.TestCase):
    """Tests for mouse state handling."""

    def test_mouse_moves_clamped_to_screen(self):
        """Absolute and relative mouse moves are clamped to staying on the screen."""
        processor = InputProcessor(600, 600)
        actions = [
            move_to_action((800, 800)),
            move_to_action((-200, -200)),
            move_mouse_action((1000, 0)),
        ]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(
            immediate,
            [
                mouse_move_event((600, 600)),
                mouse_move_event((0, 0)),
                mouse_move_event((600, 0)),
            ],
        )
        self.assertEqual(delayed, [])

    def test_relative_moves_correct_position(self):
        """Relative moves go to correct location."""
        processor = InputProcessor(600, 600)
        actions = [
            move_to_action((100, 100)),
            move_mouse_action((10, 5)),
            move_mouse_action((20, 10)),
        ]

        immediate, delayed = processor.process_input_actions(actions)

        self.assertEqual(
            immediate,
            [
                mouse_move_event((100, 100)),
                mouse_move_event((110, 105)),
                mouse_move_event((130, 115)),
            ],
        )
        self.assertEqual(delayed, [])


if __name__ == "__main__":
    unittest.main()
