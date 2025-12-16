import time

from bounce_desktop import Desktop

from bounce_rl.input.keys import KEY_0, KEY_ALT_L, KEY_BACKSPACE, KEY_TAB


def factorio_start_macro(d: Desktop):
    """Note: Expects that factorio is running around version 2.0.66 and with a
    resolution of 1000x600."""
    for i in range(20):
        print(f"Waiting {i}/20 seconds.")
        time.sleep(1)

    def click_at(x: int, y: int):
        return ((d.move_mouse, x, y), (d.mouse_press, 1), (d.mouse_release, 1))

    def press_key(k):
        return ((d.key_press, k), (d.key_release, k))

    macro = [
        *click_at(500, 185),  # Click single player
        *click_at(500, 265),  # Click new game
        *click_at(100, 80),  # Click freeplay
        *click_at(800, 570),  # Click Next
        *click_at(650, 40),  # Click Seed
        (d.key_press, KEY_BACKSPACE),  # Delete Seed string
        (time.sleep, 1),
        (d.key_release, KEY_BACKSPACE),
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
