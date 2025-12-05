"""
Gym action space integration for the BounceRL input system.

This module exposes the BounceRL input system through the Gym API, providing
a fixed-layout action space that can be masked for per-environment input restrictions.
"""

from typing import List

import numpy as np
from gym import spaces

from bounce_rl.input.allowed_inputs import AllowKeys
from bounce_rl.input.input_types import (
    InputAction,
    KeyAction,
    KeyActionType,
    drag_mouse,
    drag_mouse_to,
    move_mouse,
    move_to,
)
from bounce_rl.input.keys import (
    LEFT_MOUSE_BUTTON,
    MIDDLE_MOUSE_BUTTON,
    RIGHT_MOUSE_BUTTON,
    Digits,
    FnKeys,
    Letters,
    Modifiers,
    MouseButtons,
    Other,
    Punctuation,
    ScrollButtons,
)

# Key ordering in action space
# IMPORTANT: This list should only be extended in future versions, never reordered.
# New keys must be appended to maintain backward compatibility with trained models.
ACTION_KEYS = (
    Letters  # KEY_A through KEY_Z
    + Digits  # KEY_0 through KEY_9
    + Punctuation  # KEY_EXCLAM, KEY_AT, etc.
    + FnKeys  # F1 through F12
    + Modifiers  # KEY_SHIFT_L, KEY_ALT_L, KEY_CONTROL_L
    + Other  # Tab, Escape, Enter, Backspace
    + MouseButtons  # LEFT_MOUSE_BUTTON, RIGHT_MOUSE_BUTTON, MIDDLE_MOUSE_BUTTON
    + ScrollButtons  # SCROLL_UP, SCROLL_DOWN
)

# Tuple indices
KEYS_INDEX = 0
MOUSE_DISCRETE_INDEX = 1
MOUSE_POSITION_INDEX = 2

# Key action values
KEY_NO_OP = 0
KEY_PRESS = 1
KEY_DOWN = 2
KEY_UP = 3

# Mouse discrete indices (within action[1])
MOUSE_TRANSLATION_MODE_INDEX = 0
MOUSE_ACTION_INDEX = 1
MOUSE_DRAG_BUTTON_INDEX = 2

# Mouse translation mode values
MOUSE_ABSOLUTE = 0
MOUSE_RELATIVE = 1

# Mouse action values
MOUSE_ACTION_NONE = 0
MOUSE_ACTION_MOVE = 1
MOUSE_ACTION_DRAG = 2

# Mouse drag button values
MOUSE_DRAG_LEFT = 0
MOUSE_DRAG_RIGHT = 1
MOUSE_DRAG_MIDDLE = 2

# Map drag button indices to key values
_DRAG_BUTTON_MAP = {
    MOUSE_DRAG_LEFT: LEFT_MOUSE_BUTTON,
    MOUSE_DRAG_RIGHT: RIGHT_MOUSE_BUTTON,
    MOUSE_DRAG_MIDDLE: MIDDLE_MOUSE_BUTTON,
}


def action_space(screen_width: int, screen_height: int) -> spaces.Tuple:
    """
    Return the Gym action space for inputs.

    Args:
        screen_width: Width of the screen in pixels
        screen_height: Height of the screen in pixels

    Returns:
        A Gym Tuple space with three elements:
        - [0] MultiDiscrete for key actions - one Discrete(4) per key in ACTION_KEYS
        - [1] MultiDiscrete for mouse discrete actions - [translation_mode, action, drag_button]
        - [2] Box for mouse position - [x, y] with bounds for both absolute and relative moves
    """
    key_actions = spaces.MultiDiscrete([4] * len(ACTION_KEYS))

    mouse_discrete = spaces.MultiDiscrete([2, 3, 3])

    mouse_position = spaces.Box(
        low=np.array([-400, -400], dtype=np.float32),
        high=np.array([screen_width, screen_height], dtype=np.float32),
        dtype=np.float32,
    )

    return spaces.Tuple((key_actions, mouse_discrete, mouse_position))


def mask_action(action: tuple, allowed_inputs: AllowKeys) -> tuple:
    """
    Masks the given Gym action to only allowed inputs.

    Environments apply this automatically, but users can also use this themselves
    to normalize their actions to just the inputs that apply to an environment.

    Disallowed key actions are set to KEY_NO_OP (0).

    Args:
        action: Gym action tuple (key_actions, mouse_discrete, mouse_position)
        allowed_inputs: AllowKeys instance specifying which keys are allowed

    Returns:
        Masked action tuple with disallowed keys set to KEY_NO_OP
    """
    key_actions, mouse_discrete, mouse_position = action

    # Get the list of allowed keys
    allowed_keys = allowed_inputs.keys()
    allowed_keys_set = set(allowed_keys)

    # Make a copy of key actions to modify
    masked_key_actions = np.array(key_actions, copy=True)

    # Mask disallowed keys by setting them to KEY_NO_OP
    for i, key in enumerate(ACTION_KEYS):
        if key not in allowed_keys_set:
            masked_key_actions[i] = KEY_NO_OP

    return (masked_key_actions, mouse_discrete, mouse_position)


def process_gym_action(
    action: tuple, screen_width: int, screen_height: int
) -> List[InputAction]:
    """
    Converts a Gym action to its corresponding input actions.

    Mouse position values are clamped during processing:
    - Absolute positions: clamped to [0, screen_width] and [0, screen_height]
    - Relative positions: clamped to [-400, 400] for both x and y

    Args:
        action: Gym action tuple (key_actions, mouse_discrete, mouse_position)
        screen_width: Width of the screen in pixels
        screen_height: Height of the screen in pixels

    Returns:
        List of InputAction objects (KeyAction and/or MouseAction)
    """
    key_actions, mouse_discrete, mouse_position = action

    result = []

    # Process key actions
    for i, key_action_value in enumerate(key_actions):
        if key_action_value == KEY_NO_OP:
            continue

        key = ACTION_KEYS[i]

        if key_action_value == KEY_PRESS:
            result.append(KeyAction(action=KeyActionType.KEY_PRESS, key=key))
        elif key_action_value == KEY_DOWN:
            result.append(KeyAction(action=KeyActionType.KEY_DOWN, key=key))
        elif key_action_value == KEY_UP:
            result.append(KeyAction(action=KeyActionType.KEY_UP, key=key))

    # Process mouse actions
    translation_mode = mouse_discrete[MOUSE_TRANSLATION_MODE_INDEX]
    mouse_action_type = mouse_discrete[MOUSE_ACTION_INDEX]
    drag_button_idx = mouse_discrete[MOUSE_DRAG_BUTTON_INDEX]

    if mouse_action_type != MOUSE_ACTION_NONE:
        # Extract and clamp position
        x, y = float(mouse_position[0]), float(mouse_position[1])

        if translation_mode == MOUSE_ABSOLUTE:
            # Clamp absolute positions to screen bounds
            x = max(0, min(x, screen_width))
            y = max(0, min(y, screen_height))
            position = (int(x), int(y))

            if mouse_action_type == MOUSE_ACTION_MOVE:
                result.append(move_to(position))
            elif mouse_action_type == MOUSE_ACTION_DRAG:
                drag_button = _DRAG_BUTTON_MAP[drag_button_idx]
                result.append(drag_mouse_to(drag_button, position))

        else:  # MOUSE_RELATIVE
            # Clamp relative positions to [-400, 400]
            x = max(-400, min(x, 400))
            y = max(-400, min(y, 400))
            position = (int(x), int(y))

            if mouse_action_type == MOUSE_ACTION_MOVE:
                result.append(move_mouse(position))
            elif mouse_action_type == MOUSE_ACTION_DRAG:
                drag_button = _DRAG_BUTTON_MAP[drag_button_idx]
                result.append(drag_mouse(drag_button, position))

    return result
