"""Tests for gym_input.py"""

import unittest

import numpy as np
from gymnasium import spaces

from bounce_rl.input.allowed_inputs import AllowKeys
from bounce_rl.input.gym_input import (
    ACTION_KEYCODES,
    MAX_BUTTON_ACTIONS,
    action_space,
    mask_action,
    no_op_gym_action,
    process_gym_action,
)
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
from bounce_rl.input.keys import BTN_LEFT, KEY_A, KEY_B


class TestActionSpace(unittest.TestCase):
    def test_no_op_action_is_in_action_space(self):
        self.assertTrue(action_space(800, 600).contains(no_op_gym_action()))


class TestMaskAction(unittest.TestCase):
    def test_mask_action_masks_disallowed_keys(self):
        action = no_op_gym_action()
        action["keys"][0] = [ACTION_KEYCODES.index(KEY_A), KeyActionKind.KEY_PRESS]
        action["keys"][1] = [ACTION_KEYCODES.index(KEY_B), KeyActionKind.KEY_DOWN]

        masked_action = mask_action(action, AllowKeys([KEY_B]))

        self.assertEqual(masked_action["keys"][0][1], KeyActionKind.KEY_ACTION_NONE)
        self.assertEqual(masked_action["keys"][1][1], KeyActionKind.KEY_DOWN)

    def test_mask_action_does_not_mutate_original_action(self):
        action = no_op_gym_action()
        action["keys"][0] = [ACTION_KEYCODES.index(KEY_A), KeyActionKind.KEY_PRESS]

        mask_action(action, AllowKeys([]))

        self.assertEqual(action["keys"][0][1], KeyActionKind.KEY_PRESS)


class TestProcessGymAction(unittest.TestCase):
    def test_process_gym_action_generates_key_actions(self):
        action = no_op_gym_action()
        action["keys"][0] = [ACTION_KEYCODES.index(KEY_A), KeyActionKind.KEY_PRESS]
        action["keys"][1] = [ACTION_KEYCODES.index(KEY_B), KeyActionKind.KEY_DOWN]

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [
                KeyAction(action=KeyActionKind.KEY_PRESS, keycode=KEY_A),
                KeyAction(action=KeyActionKind.KEY_DOWN, keycode=KEY_B),
            ],
        )

    def test_process_gym_action_handles_no_op(self):
        self.assertEqual(process_gym_action(no_op_gym_action(), 800, 600), [])

    def test_process_gym_action_generates_mouse_move(self):
        action = no_op_gym_action()
        action["mouse_action"]["action"] = MouseActionKind.MOVE
        action["mouse_action"]["target"] = np.array([1, -1], dtype=np.float32)

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [MouseMoveAction(position=(800, 0))],
        )

    def test_process_gym_action_clamps_mouse_target(self):
        action = no_op_gym_action()
        action["mouse_action"]["action"] = MouseActionKind.MOVE
        action["mouse_action"]["target"] = np.array([2, -2], dtype=np.float32)

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [MouseMoveAction(position=(800, 0))],
        )

    def test_process_gym_action_generates_mouse_button_action(self):
        action = no_op_gym_action()
        action["mouse_action"]["button"] = 0
        action["mouse_action"]["action"] = MouseActionKind.BTN_PRESS

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [
                MouseMoveAction(position=(400, 300)),
                MouseButtonAction(action=MouseActionKind.BTN_PRESS, button=BTN_LEFT),
            ],
        )

    def test_process_gym_action_generates_drag_sequence(self):
        action = no_op_gym_action()
        action["mouse_action"]["button"] = 0
        action["mouse_action"]["action"] = MouseActionKind.DRAG
        action["mouse_action"]["drag_start"] = np.array([-1, -1], dtype=np.float32)
        action["mouse_action"]["target"] = np.array([1, 1], dtype=np.float32)

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [MouseDragAction(start=(0, 0), end=(800, 600), button=BTN_LEFT)],
        )

    def test_process_gym_action_generates_scroll_action(self):
        action = no_op_gym_action()
        action["scroll"] = KeyDirection.KEY_DOWN

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [ScrollAction(direction=KeyDirection.KEY_DOWN)],
        )

    def test_process_gym_action_accepts_explicit_mouse_no_op(self):
        action = no_op_gym_action()
        action["mouse_action"]["action"] = MouseActionKind.NONE
        action["mouse_action"]["target"] = np.array([1, 1], dtype=np.float32)

        self.assertEqual(process_gym_action(action, 800, 600), [])


if __name__ == "__main__":
    unittest.main()
