from harness import *

# model interface
#   get_action(bitmap) returns a keymap to use

harness = Harness()
model = Model()

while harness.tick():
    bitmap = harness.get_screen()
    if bitmap is not None:
        keymap = model.get_action(bitmap)
        harness.perform_actions(keymap)
