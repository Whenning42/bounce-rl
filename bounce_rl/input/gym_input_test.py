"""Tests for gym_input.py"""

import unittest

import numpy as np

from bounce_rl.input.allowed_inputs import DisallowKeys
from bounce_rl.input.gym_input import (
    ACTION_KEYS,
    KEY_DOWN,
    KEY_NO_OP,
    KEY_PRESS,
    KEY_UP,
    KEYS_INDEX,
    MOUSE_ABSOLUTE,
    MOUSE_ACTION_DRAG,
    MOUSE_ACTION_MOVE,
    MOUSE_ACTION_NONE,
    MOUSE_DISCRETE_INDEX,
    MOUSE_DRAG_LEFT,
    MOUSE_DRAG_RIGHT,
    MOUSE_POSITION_INDEX,
    MOUSE_RELATIVE,
    action_space,
    mask_action,
    process_gym_action,
)
from bounce_rl.input.input_types import KeyAction, KeyActionType, MouseAction
from bounce_rl.input.keys import (
    KEY_A,
    KEY_B,
    KEY_C,
    LEFT_MOUSE_BUTTON,
    MIDDLE_MOUSE_BUTTON,
    RIGHT_MOUSE_BUTTON,
)


def no_op_gym_action():
    """Create a no-op gym action (all keys no-op, no mouse action)."""
    key_actions = np.zeros(len(ACTION_KEYS), dtype=int)
    mouse_discrete = np.array([MOUSE_ABSOLUTE, MOUSE_ACTION_NONE, MOUSE_DRAG_LEFT])
    mouse_position = np.array([0, 0])
    return [key_actions, mouse_discrete, mouse_position]


class TestActionSpace(unittest.TestCase):
    """Tests for action_space function."""

    def test_action_space_structure(self):
        """Verify action space has correct structure."""
        space = action_space(800, 600)

        # Should be a Tuple space with 3 elements
        self.assertEqual(len(space.spaces), 3)

        # First element: MultiDiscrete for keys
        key_space = space.spaces[0]
        self.assertEqual(len(key_space.nvec), len(ACTION_KEYS))
        self.assertTrue(all(n == 4 for n in key_space.nvec))

        # Second element: MultiDiscrete for mouse discrete
        mouse_discrete_space = space.spaces[1]
        self.assertEqual(len(mouse_discrete_space.nvec), 3)
        self.assertEqual(list(mouse_discrete_space.nvec), [2, 3, 3])

        # Third element: Box for mouse position
        mouse_pos_space = space.spaces[2]
        self.assertEqual(mouse_pos_space.shape, (2,))
        np.testing.assert_array_equal(mouse_pos_space.low, [-400, -400])
        np.testing.assert_array_equal(mouse_pos_space.high, [800, 600])


class TestMaskAction(unittest.TestCase):
    """Tests for mask_action function."""

    def test_mask_action_masks_disallowed_keys(self):
        """Verify that disallowed keys are set to no-op while allowed keys are
        unchanged."""
        # Create action with all keys set to KEY_PRESS
        action = no_op_gym_action()
        action[KEYS_INDEX] = np.ones(len(ACTION_KEYS), dtype=int)

        # Mask action to disallow KEY_A and KEY_B
        masked_action = mask_action(
            action, DisallowKeys([KEY_A, KEY_B]).to_allow_list()
        )

        # Disallowed keys should be KEY_NO_OP, others should remain KEY_PRESS
        masked_key_actions = masked_action[KEYS_INDEX]
        self.assertEqual(masked_key_actions[ACTION_KEYS.index(KEY_A)], KEY_NO_OP)
        self.assertEqual(masked_key_actions[ACTION_KEYS.index(KEY_B)], KEY_NO_OP)

        for i, key in enumerate(ACTION_KEYS):
            if key not in [KEY_A, KEY_B]:
                self.assertEqual(masked_key_actions[i], KEY_PRESS)

        np.testing.assert_array_equal(
            masked_action[MOUSE_DISCRETE_INDEX], action[MOUSE_DISCRETE_INDEX]
        )
        np.testing.assert_array_equal(
            masked_action[MOUSE_POSITION_INDEX], action[MOUSE_POSITION_INDEX]
        )

    def test_mask_action_masks_disallowed_mouse_buttons(self):
        """Verify that disallowed mouse buttons are set to no-op while other keys are
        unchanged."""
        # Create action with all keys set to KEY_PRESS
        action = no_op_gym_action()
        action[KEYS_INDEX] = np.ones(len(ACTION_KEYS), dtype=int)

        # Mask action to disallow left and right mouse buttons
        masked_action = mask_action(
            action,
            DisallowKeys([LEFT_MOUSE_BUTTON, RIGHT_MOUSE_BUTTON]).to_allow_list(),
        )

        # Disallowed mouse buttons should be KEY_NO_OP, others should remain KEY_PRESS
        masked_key_actions = masked_action[KEYS_INDEX]
        self.assertEqual(
            masked_key_actions[ACTION_KEYS.index(LEFT_MOUSE_BUTTON)], KEY_NO_OP
        )
        self.assertEqual(
            masked_key_actions[ACTION_KEYS.index(RIGHT_MOUSE_BUTTON)], KEY_NO_OP
        )
        self.assertEqual(
            masked_key_actions[ACTION_KEYS.index(MIDDLE_MOUSE_BUTTON)], KEY_PRESS
        )
        self.assertEqual(masked_key_actions[ACTION_KEYS.index(KEY_A)], KEY_PRESS)

        np.testing.assert_array_equal(
            masked_action[MOUSE_DISCRETE_INDEX], action[MOUSE_DISCRETE_INDEX]
        )
        np.testing.assert_array_equal(
            masked_action[MOUSE_POSITION_INDEX], action[MOUSE_POSITION_INDEX]
        )


class TestProcessGymAction(unittest.TestCase):
    """Tests for process_gym_action function."""

    def test_process_gym_action_generates_key_actions(self):
        """Verify that key actions are correctly converted to InputActions."""
        # Setup gym action with specific key actions
        action = no_op_gym_action()
        action[KEYS_INDEX][ACTION_KEYS.index(KEY_A)] = KEY_PRESS
        action[KEYS_INDEX][ACTION_KEYS.index(KEY_B)] = KEY_DOWN
        action[KEYS_INDEX][ACTION_KEYS.index(KEY_C)] = KEY_UP

        # Process the action
        result = process_gym_action(action, 800, 600)

        # Should generate expected key actions (ordered by ACTION_KEYS)
        expected = [
            KeyAction(action=KeyActionType.KEY_PRESS, key=KEY_A),
            KeyAction(action=KeyActionType.KEY_DOWN, key=KEY_B),
            KeyAction(action=KeyActionType.KEY_UP, key=KEY_C),
        ]
        self.assertEqual(result, expected)

    def test_process_gym_action_relative_move(self):
        """Verify that relative mouse move is correctly converted."""
        action = no_op_gym_action()
        action[MOUSE_DISCRETE_INDEX] = np.array(
            [MOUSE_RELATIVE, MOUSE_ACTION_MOVE, MOUSE_DRAG_LEFT]
        )
        action[MOUSE_POSITION_INDEX] = np.array([10, 20])

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [
                MouseAction(
                    is_relative=True, position=(10, 20), is_drag=False, drag_button=None
                )
            ],
        )

    def test_process_gym_action_absolute_move(self):
        """Verify that absolute mouse move is correctly converted."""
        action = no_op_gym_action()
        action[MOUSE_DISCRETE_INDEX] = np.array(
            [MOUSE_ABSOLUTE, MOUSE_ACTION_MOVE, MOUSE_DRAG_LEFT]
        )
        action[MOUSE_POSITION_INDEX] = np.array([100, 200])

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [
                MouseAction(
                    is_relative=False,
                    position=(100, 200),
                    is_drag=False,
                    drag_button=None,
                )
            ],
        )

    def test_process_gym_action_relative_drag(self):
        """Verify that relative mouse drag is correctly converted."""
        action = no_op_gym_action()
        action[MOUSE_DISCRETE_INDEX] = np.array(
            [MOUSE_RELATIVE, MOUSE_ACTION_DRAG, MOUSE_DRAG_RIGHT]
        )
        action[MOUSE_POSITION_INDEX] = np.array([5, -10])

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [
                MouseAction(
                    is_relative=True,
                    position=(5, -10),
                    is_drag=True,
                    drag_button=RIGHT_MOUSE_BUTTON,
                )
            ],
        )

    def test_process_gym_action_clamps_absolute_positions(self):
        """Verify that absolute positions are clamped to screen bounds."""
        action = no_op_gym_action()
        action[MOUSE_DISCRETE_INDEX] = np.array(
            [MOUSE_ABSOLUTE, MOUSE_ACTION_MOVE, MOUSE_DRAG_LEFT]
        )
        action[MOUSE_POSITION_INDEX] = np.array([1000, -200])

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [
                MouseAction(
                    is_relative=False,
                    position=(800, 0),
                    is_drag=False,
                    drag_button=None,
                )
            ],
        )

    def test_process_gym_action_clamps_relative_positions(self):
        """Verify that relative positions are clamped to [-400, 400]."""
        action = no_op_gym_action()
        action[MOUSE_DISCRETE_INDEX] = np.array(
            [MOUSE_RELATIVE, MOUSE_ACTION_MOVE, MOUSE_DRAG_LEFT]
        )
        action[MOUSE_POSITION_INDEX] = np.array([1000, -500])

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [
                MouseAction(
                    is_relative=True,
                    position=(400, -400),
                    is_drag=False,
                    drag_button=None,
                )
            ],
        )

    def test_process_gym_action_handles_no_mouse_action(self):
        """Verify that MOUSE_ACTION_NONE produces no mouse action."""
        action = no_op_gym_action()
        action[MOUSE_POSITION_INDEX] = np.array([100, 200])

        result = process_gym_action(action, 800, 600)
        self.assertEqual(len(result), 0)  # No actions generated

    def test_process_gym_action_generates_both_key_and_mouse_actions(self):
        """Verify that both key and mouse actions can be generated from single gym
        action."""
        action = no_op_gym_action()
        action[KEYS_INDEX][ACTION_KEYS.index(KEY_A)] = KEY_PRESS
        action[MOUSE_DISCRETE_INDEX] = np.array(
            [MOUSE_RELATIVE, MOUSE_ACTION_MOVE, MOUSE_DRAG_LEFT]
        )
        action[MOUSE_POSITION_INDEX] = np.array([10, 20])

        result = process_gym_action(action, 800, 600)

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], KeyAction)
        self.assertIsInstance(result[1], MouseAction)


if __name__ == "__main__":
    unittest.main()
