"""
Input action processor for the BounceRL input system.

This module manages keyboard and mouse state and converts high-level input actions
into low-level input events, handling state transitions and casing logic.
"""

from typing import List

from bounce_rl.input.input_types import (
    InputAction,
    InputEvent,
    KeyAction,
    KeyActionType,
    KeyDirection,
    KeyEvent,
    MouseAction,
    key_down_event,
    key_up_event,
    mouse_move_event,
)
from bounce_rl.input.keys import KEY_SHIFT_L, LOWERCASE_OFFSET, Letters


class InputProcessor:
    """
    Processes input actions into input events with state management.

    Manages keyboard state (which keys are pressed, shift state for casing) and
    mouse state (current position) to generate correct event sequences.
    """

    def __init__(self, screen_x: int, screen_y: int):
        """
        Initialize the input processor.

        Args:
            screen_x: Screen width in pixels, used to clamp the pointer to the screen
            screen_y: Screen height in pixels, used to clamp the pointer to the screen
        """
        self._screen_x = screen_x
        self._screen_y = screen_y

        # Track which keys are currently pressed (maps key -> actual keysym pressed)
        # For letters, this tracks the cased version that was actually pressed
        self._pressed_keys_keysyms: dict[int, int] = {}

        self._shift_pressed = False

        self._mouse_x = 0
        self._mouse_y = 0

    def process_input_actions(
        self, actions: List[InputAction]
    ) -> tuple[List[InputEvent], List[InputEvent]]:
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
            if isinstance(action, KeyAction):
                imm, dly = self._process_key_action(action)
            elif isinstance(action, MouseAction):
                imm, dly = self._process_mouse_action(action)
            immediate.extend(imm)
            delayed.extend(dly)

        return immediate, delayed

    def release_buttons(self) -> List[KeyEvent]:
        """
        Release all currently held buttons.

        Useful when resetting an environment to ensure clean state.

        Returns:
            List of KeyUp events for all currently pressed keys
        """
        events = []
        for keysym in list(self._pressed_keys_keysyms.values()):
            events.append(KeyEvent(action=KeyDirection.KEY_UP, keysym=keysym))
        self._pressed_keys_keysyms = {}
        self._shift_pressed = False
        return events

    def _process_key_action(
        self, action: KeyAction
    ) -> tuple[List[KeyEvent], List[KeyEvent]]:
        if action.action == KeyActionType.KEY_DOWN:
            return self._key_down(action.key), []
        elif action.action == KeyActionType.KEY_UP:
            return self._key_up(action.key), []
        elif action.action == KeyActionType.KEY_PRESS:
            immediate = []
            delayed = []
            if action.key in self._pressed_keys_keysyms:
                immediate.extend(self._key_up(action.key))
            immediate.extend(self._key_down(action.key))
            delayed.extend(self._key_up(action.key))
            return immediate, delayed

    def _process_mouse_action(
        self, action: MouseAction
    ) -> tuple[List[KeyEvent], List[KeyEvent]]:
        """Process a mouse action into events."""
        if action.is_relative:
            target_x = self._mouse_x + action.position[0]
            target_y = self._mouse_y + action.position[1]
        else:
            target_x = action.position[0]
            target_y = action.position[1]

        target_x = max(0, min(target_x, self._screen_x))
        target_y = max(0, min(target_y, self._screen_y))
        self._mouse_x = target_x
        self._mouse_y = target_y

        if action.is_drag:
            return [
                key_down_event(action.drag_button),
                mouse_move_event((target_x, target_y)),
            ], [key_up_event(action.drag_button)]
        else:
            return [mouse_move_event((target_x, target_y))], []

    def _key_down(self, key: int) -> List[KeyEvent]:
        """
        Handle key down action with state management.

        Returns list of events (empty if key is already pressed).
        """
        if key in self._pressed_keys_keysyms:
            return []

        if key == KEY_SHIFT_L:
            self._shift_pressed = True

        keysym = self._get_keysym(key, self._shift_pressed)
        self._pressed_keys_keysyms[key] = keysym
        return [key_down_event(keysym)]

    def _key_up(self, key: int) -> List[KeyEvent]:
        """
        Handle key up action with state management.

        Returns list of events (may be empty if key not pressed).
        """
        if key not in self._pressed_keys_keysyms:
            return []

        if key == KEY_SHIFT_L:
            self._shift_pressed = False

        keysym = self._pressed_keys_keysyms[key]
        del self._pressed_keys_keysyms[key]
        return [key_up_event(keysym)]

    def _get_keysym(self, key: int, shift_pressed: bool) -> int:
        if key not in Letters or shift_pressed:
            return key
        else:  # in Letters and not self._shift_pressed
            return key + LOWERCASE_OFFSET
