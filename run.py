from harness import *

# model interface
#   get_action(bitmap) returns a keymap to use

harness = Harness()
model = Model()

while harness.tick():
    bitmap = harness.get_screen()
    keymap = model.get_action(bitmap)
    harness.perform_actions(keymap)
