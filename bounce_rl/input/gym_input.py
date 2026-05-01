"""
Gym action space integration for the BounceRL input system.

This module exposes the BounceRL input system through the Gym API, providing
a fixed-layout action space that can be masked for per-environment input restrictions.
"""

import numpy as np
from gymnasium import spaces
import copy

from bounce_rl.input.allowed_inputs import AllowKeys
from bounce_rl.input.input_types import (
    InputAction,
    KeyAction,
    KeyActionKind,
    KeyDirection,
    MouseMoveAction,
    MouseButtonAction,
    MouseDragAction,
    ScrollAction,
    MouseActionKind,
)
from bounce_rl.input.keys import (
    FnKeys,
    Letters,
    Modifiers,
    MouseButtons,
    Other,
    Symbols,
)

# Key ordering in action space
# IMPORTANT: This list should only be extended in future versions, never reordered.
# New keys must be appended to maintain backward compatibility with trained models.
ACTION_KEYCODES = Letters + Symbols + FnKeys + Modifiers + Other

MAX_BUTTON_ACTIONS = 8

_keys_shape = (MAX_BUTTON_ACTIONS, 2)
_mouse_pos_shape = (2,)


def action_space(
    screen_width: int | None = None, screen_height: int | None = None
) -> spaces.Dict:
    def mouse_pos_space():
        return spaces.Box(
            low=np.array([-1, -1]), high=np.array([1, 1]), dtype=np.float32
        )

    return spaces.Dict(
        {
            "keys": spaces.MultiDiscrete(
                np.array(
                    [
                        [len(ACTION_KEYCODES), len(KeyActionKind)]
                        for i in range(MAX_BUTTON_ACTIONS)
                    ]
                )
            ),
            "mouse_action": spaces.Dict(
                {
                    "button": spaces.Discrete(len(MouseButtons)),
                    "action": spaces.Discrete(len(MouseActionKind)),
                    "drag_start": mouse_pos_space(),
                    "target": mouse_pos_space(),
                }
            ),
            "scroll": spaces.Discrete(len(KeyDirection)),
        }
    )


def mask_action(action: dict, allowed_inputs: AllowKeys) -> dict:
    """Masks the given Gym action to only allowed inputs."""
    action = copy.deepcopy(action)
    allowed_keycodes = set(allowed_inputs.keycodes())
    for act in action["keys"]:  # type: ignore
        key_idx, _ = act
        keycode = ACTION_KEYCODES[int(key_idx)]
        if keycode not in allowed_keycodes:
            act[1] = KeyActionKind.KEY_ACTION_NONE
    return action


def no_op_gym_action() -> dict:
    """Create a no-op gym action (all keys no-op, no mouse action)."""
    return {
        "keys": np.zeros(_keys_shape, dtype=int),
        "mouse_action": {
            "button": 0,
            "action": MouseActionKind.NONE,
            "drag_start": np.zeros(_mouse_pos_shape, dtype=np.float32),
            "target": np.zeros(_mouse_pos_shape, dtype=np.float32),
        },
        "scroll": KeyDirection.KEY_NO_DIRECTION,
    }


def _screen_position(
    normalized_position: np.ndarray | tuple[float, float] | list[float],
    screen_width: int,
    screen_height: int,
) -> tuple[int, int]:
    x = float(np.clip(normalized_position[0], -1, 1))
    y = float(np.clip(normalized_position[1], -1, 1))
    return (int((x + 1) * screen_width / 2), int((y + 1) * screen_height / 2))


def process_gym_action(
    action: dict, screen_width: int, screen_height: int
) -> list[InputAction]:
    """Converts a Gym action to its corresponding input actions."""
    out = []

    def pos(p):
        return _screen_position(p, screen_width, screen_height)

    # keys
    for key_idx, action_type in action["keys"]:
        if action_type == KeyActionKind.KEY_ACTION_NONE:
            continue
        keycode = ACTION_KEYCODES[int(key_idx)]
        out.append(KeyAction(action=action_type, keycode=keycode))

    # mouse_action
    mouse_action = action["mouse_action"]["action"]
    mouse_button_idx = action["mouse_action"]["button"]
    target = action["mouse_action"]["target"]
    if mouse_action == MouseActionKind.MOVE:
        out.append(MouseMoveAction(pos(target)))

    elif mouse_action == MouseActionKind.DRAG:
        drag_start = action["mouse_action"]["drag_start"]
        out.append(
            MouseDragAction(
                pos(drag_start),
                pos(target),
                MouseButtons[mouse_button_idx],
            )
        )

    elif mouse_action in (
        MouseActionKind.BTN_PRESS,
        MouseActionKind.BTN_DOWN,
        MouseActionKind.BTN_UP,
    ):
        out.append(MouseMoveAction(pos(target)))
        out.append(MouseButtonAction(mouse_action, MouseButtons[mouse_button_idx]))

    elif mouse_action == MouseActionKind.NONE:
        pass

    else:
        assert False

    # scroll
    scroll_direction = action["scroll"]
    if scroll_direction != KeyDirection.KEY_NO_DIRECTION:
        out.append(ScrollAction(direction=scroll_direction))

    return out
