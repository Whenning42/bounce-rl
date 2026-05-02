import time

from bounce_desktop import Desktop

from bounce_rl.environments.factorio_matcher import FactorioMatcher
from bounce_rl.input.keys import KEY_0, KEY_ALT_L, KEY_BACKSPACE, KEY_TAB


def factorio_start_macro(d: Desktop):
    """Note: Expects that factorio is running around version 2.0.66 and with a
    resolution of 1000x600."""

    matcher = FactorioMatcher()
    for i in range(60):
        print(f"Waiting {i}/60 seconds.")
        f = d.get_frame()
        if matcher.check_if_on_main_menu(f):
            break
        time.sleep(1)

    f = d.get_frame()
    if not matcher.check_if_on_main_menu(f):
        raise ValueError("Failed to initialize factorio environment.")

    def click_at(x: int, y: int):
        return ((d.move_mouse_to, x, y), (d.mouse_press, 1), (d.mouse_release, 1))

    def press_key(k):
        return ((d.keycode_down, k), (d.keycode_up, k))

    macro = [
        *click_at(500, 185),  # Click single player
        *click_at(500, 265),  # Click new game
        *click_at(100, 80),  # Click freeplay
        *click_at(800, 570),  # Click Next
        *click_at(650, 40),  # Click Seed
        (d.keycode_down, KEY_BACKSPACE),  # Delete Seed string
        (time.sleep, 1),
        (d.keycode_up, KEY_BACKSPACE),
        *press_key(KEY_0),  # Type "0" for the seed
        *click_at(600, 570),  # Click play
        (time.sleep, 1),
        *press_key(KEY_TAB),  # Press tab to skip intro pan
        *press_key(KEY_ALT_L),  # Press alt to enter alt item view mode
    ]

    for action in macro:
        fn, *args = action
        fn(*args)
        time.sleep(0.2)
