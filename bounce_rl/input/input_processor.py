"""
Input action processor for the BounceRL input system.

This module manages keyboard and mouse state and converts high-level input actions
into low-level input events, handling state transitions and casing logic.
"""

from typing import List

from bounce_rl.input.input_types import (
    InputAction,
    KeyAction,
    ButtonActionKind,
    MouseButtonAction,
)
from bounce_rl.input.keys import MouseButtons

ButtonCode = int


class InputProcessor:
    """
    Processes input actions into input events with state management.

    Manages keyboard state (which keys are pressed, shift state for casing) and
    mouse state (current position) to generate correct event sequences.
    """

    def __init__(self, screen_x: int, screen_y: int):
        self._screen_x = screen_x
        self._screen_y = screen_y
        self._pressed_buttons: set[ButtonCode] = set()

    def process_input_actions(
        self, actions: List[InputAction]
    ) -> tuple[List[InputAction], List[InputAction]]:
        """
        Convert input actions to input events with state management.

        Returns two lists of events:
        1. Events that callers should issue immediately
        2. Events that callers should issue after some delay if they want
           polling-based apps to see input action intermediate button states

        For example: a keyPress action generates a keyDown event in the first
        list and a keyUp event in the second. By issuing these events with a
        small delay in between (say 50ms), polling-based apps have the chance
        to see the key-down state before the key is released.

        Compound actions map as:
          KeyPress -> ([KeyDown], [KeyUp])
          MouseDrag -> ([ButtonDown, MoveMouse], [ButtonUp])

        Args:
            actions: List of input actions to process

        Returns:
            Tuple of (immediate_events, delayed_events)
        """
        immediate = []
        delayed = []

        for action in actions:
            if isinstance(action, (KeyAction, MouseButtonAction)):
                imm, dly = self._process_button_action(action)
                immediate.extend(imm)
                delayed.extend(dly)
            else:
                immediate.append(action)
        return immediate, delayed

    def release_buttons(self) -> List[KeyAction]:
        """Release all currently held buttons.

        Useful when resetting an environment to ensure clean state."""
        out = []
        for button in list(self._pressed_buttons):
            if button in MouseButtons:
                out.append(MouseButtonAction.up(button))
            else:
                out.append(KeyAction.up(button))
        self._pressed_buttons = set()
        return out

    def _process_button_action(
        self, action: KeyAction | MouseButtonAction
    ) -> tuple[List[InputAction], List[InputAction]]:
        action_kind = ButtonActionKind(int(action.action))
        button = action.get_button()

        if action_kind == ButtonActionKind.NONE:
            return [], []

        cls = type(action)
        if action_kind == ButtonActionKind.DOWN:
            self._pressed_buttons.add(button)
            return [cls.down(button)], []
        elif action_kind == ButtonActionKind.UP:
            self._pressed_buttons.remove(button)
            return [cls.up(button)], []
        elif action_kind == ButtonActionKind.PRESS:
            return [cls.down(button)], [cls.up(button)]
        else:
            assert False
