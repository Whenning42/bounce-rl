"""
Benchmark for the BounceRL input system.

This module benchmarks the end-to-end performance of processing Gym actions
through the input system and dispatching events to a desktop backend.
"""

import copy
import time

import numpy as np

from bounce_rl.input.event_dispatch import apply_events_to_desktop
from bounce_rl.input.gym_input import (
    ACTION_KEYCODES,
    no_op_gym_action,
    process_gym_action,
)
from bounce_rl.input.input_processor import InputProcessor
from bounce_rl.input.input_types import KeyActionKind, MouseActionKind


class FakeDesktop:
    """
    Fake desktop backend for benchmarking.

    Implements the same event interface as Bounce Desktop with no-op methods.
    """

    def keycode_down(self, keycode: int) -> None:
        pass

    def keycode_up(self, keycode: int) -> None:
        pass

    def move_mouse(self, x: int, y: int) -> None:
        pass

    def move_mouse_to(self, x: int, y: int) -> None:
        pass

    def mouse_press(self, button: int) -> None:
        pass

    def mouse_release(self, button: int) -> None:
        pass


def _create_benchmark_action(use_mouse_move: bool) -> dict:
    """
    Create a benchmark action using the current dict-shaped Gym input API.

    Key slots are filled with a deterministic mix of no-op and press actions.
    Mouse movement alternates between a centered no-op and a move to exercise
    both paths without sending compound mouse actions to dispatch.
    """
    action = no_op_gym_action()

    for i in range(min(len(action["keys"]), len(ACTION_KEYCODES))):
        keycode = ACTION_KEYCODES[i]
        remainder = keycode % 4
        if remainder == 0:
            action_kind = KeyActionKind.KEY_ACTION_NONE
        elif remainder == 1:
            action_kind = KeyActionKind.KEY_PRESS
        else:
            action_kind = KeyActionKind.KEY_PRESS

        action["keys"][i] = np.array([i, action_kind], dtype=int)

    if use_mouse_move:
        action["mouse_action"]["action"] = MouseActionKind.MOVE
        action["mouse_action"]["target"] = np.array([0.25, -0.25], dtype=np.float32)

    return action


# Pre-create benchmark actions.
benchmark_action_a = _create_benchmark_action(use_mouse_move=True)
benchmark_action_b = _create_benchmark_action(use_mouse_move=False)


def benchmark_input_system(loop_iters: int = 100_000) -> float:
    """
    Runs the end-to-end input system benchmark and returns
    the average time in seconds to process and dispatch a new input.
    """
    input_processor = InputProcessor(800, 600)
    desktop = FakeDesktop()

    start_time = time.perf_counter()

    for i in range(loop_iters):
        if i % 2 == 0:
            action = benchmark_action_a
        else:
            action = benchmark_action_b

        input_actions = process_gym_action(copy.deepcopy(action), 800, 600)
        immediate_events, delayed_events = input_processor.process_input_actions(
            input_actions
        )
        apply_events_to_desktop(immediate_events, desktop)
        apply_events_to_desktop(delayed_events, desktop)

    end_time = time.perf_counter()
    total_loop_time = end_time - start_time

    return total_loop_time / loop_iters


if __name__ == "__main__":
    print(
        f"Action input handling takes {benchmark_input_system() * 1_000_000} microseconds"
    )
