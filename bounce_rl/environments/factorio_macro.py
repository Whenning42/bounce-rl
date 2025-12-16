import time

from bounce_desktop import Desktop

from bounce_rl.input.keys import KEY_0, KEY_ALT_L, KEY_BACKSPACE, KEY_TAB


def factorio_start_macro(d: Desktop):
    """Note: Expects that factorio is running around version 2.0.66 and with a
    resolution of 1000x600."""
    for i in range(20):
        print(f"Waiting {i}/20 seconds.")
        time.sleep(1)

    click = ((d.mouse_press, (1,)), (d.mouse_release, (1,)))
    macro = [
        (d.move_mouse, (500, 185)),  # Hover single player
        *click,
        (d.move_mouse, (500, 265)),
        *click,
        (d.move_mouse, (100, 80)),  # Hover over freeplay
        *click,
        (d.move_mouse, (800, 570)),  # Hover over Next
        *click,
        (d.move_mouse, (650, 40)),  # Hover over Seed
        *click,
        (d.key_press, (KEY_BACKSPACE,)),  # Delete Seed string
        (time.sleep, (1,)),
        (d.key_release, (KEY_BACKSPACE,)),
        (d.key_press, (KEY_0,)),  # Type "0" for the seed
        (d.key_release, (KEY_0,)),
        (d.move_mouse, (600, 570)),  # Hover over "Play"
        *click,
        (time.sleep, (1,)),
        (d.key_press, (KEY_TAB,)),  # Press tab to skip intro pan
        (d.key_release, (KEY_TAB,)),
        (d.key_press, (KEY_ALT_L,)),  # Press alt to enter alt item view mode
        (d.key_release, (KEY_ALT_L,)),
    ]

    for action in macro:
        fn, args = action
        fn(*args)
        time.sleep(0.2)
