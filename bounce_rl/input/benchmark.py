"""
Benchmark for the BounceRL input system.

This module benchmarks the end-to-end performance of processing Gym actions
through the input system and dispatching events to a desktop backend.

As of 2025/12/06, the end-to-end input handling takes ~100 microseconds
"""

import time

import numpy as np

from bounce_rl.input.event_dispatch import apply_events_to_desktop
from bounce_rl.input.gym_input import (
    ACTION_KEYS,
    KEY_DOWN,
    KEY_NO_OP,
    KEY_PRESS,
    KEY_UP,
    MOUSE_ACTION_MOVE,
    MOUSE_DRAG_LEFT,
    MOUSE_RELATIVE,
    process_gym_action,
)
from bounce_rl.input.input_processor import InputProcessor


class FakeDesktop:
    """
    Fake desktop backend for benchmarking.

    Implements the same event interface as Bounce Desktop with no-op methods.
    """

    def key_press(self, keysym: int) -> None:
        pass

    def key_release(self, keysym: int) -> None:
        pass

    def move_mouse(self, x: int, y: int) -> None:
        pass

    def mouse_press(self, button: int) -> None:
        pass

    def mouse_release(self, button: int) -> None:
        pass


def _create_benchmark_action(use_key_down: bool) -> tuple:
    """
    Create a benchmark action based on keysym values.

    For keys in the action space with keysym ≡ 0, 1 (mod 4): no-op
    For keys in the action space with keysym ≡ 2 (mod 4): press the key
    For keys in the action space with keysym ≡ 3 (mod 4):
        - if use_key_down=True: press down
        - if use_key_down=False: release key
    For mouse: move relative (10, 10)

    Args:
        use_key_down: If True, use KEY_DOWN for mod 3 keys; if False, use KEY_UP

    Returns:
        Gym action tuple (key_actions, mouse_discrete, mouse_position)
    """
    key_actions = np.zeros(len(ACTION_KEYS), dtype=int)

    for i, keysym in enumerate(ACTION_KEYS):
        remainder = keysym % 4
        if remainder == 0 or remainder == 1:
            key_actions[i] = KEY_NO_OP
        elif remainder == 2:
            key_actions[i] = KEY_PRESS
        else:  # remainder == 3
            key_actions[i] = KEY_DOWN if use_key_down else KEY_UP

    mouse_discrete = np.array([MOUSE_RELATIVE, MOUSE_ACTION_MOVE, MOUSE_DRAG_LEFT])
    mouse_position = np.array([10, 10])

    return (key_actions, mouse_discrete, mouse_position)


# Pre-create benchmark actions
benchmark_action_a = _create_benchmark_action(use_key_down=True)
benchmark_action_b = _create_benchmark_action(use_key_down=False)


def benchmark_input_system(loop_iters: int = 100_000) -> float:
    """
    Runs the end-to-end input system benchmark and returns
    the average time in seconds to process and dispatch a new input.

    Args:
        loop_iters: Number of iterations to run

    Returns:
        Average time in seconds per iteration
    """
    input_processor = InputProcessor(800, 600)
    desktop = FakeDesktop()

    start_time = time.perf_counter()

    for i in range(loop_iters):
        if i % 2 == 0:
            action = benchmark_action_a
        else:
            action = benchmark_action_b
        input_actions = process_gym_action(action, 800, 600)
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
