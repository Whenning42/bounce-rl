import rewards.noita_env
import time
from Xlib import display
import gc
from harness import Harness
import random
import objgraph

# Reproduces the error, but doesn't give granular feedback.
env = rewards.noita_env.NoitaEnv(out_dir='/tmp')

print("Starting reset loop")
i = 0
while True:
    i += 1
    print("Reset count: ", i)

    harnesses = []
    for obj in gc.get_objects():
        if isinstance(obj, Harness):
            harnesses.append(obj)
    print("Harnesses found: ", len(harnesses))

    if len(harnesses) > 17:
        h = random.choice(harnesses)
        objgraph.show_refs([h], filename=f'/tmp/harness_objgraph.png')
        objgraph.show_backrefs([h], filename=f'/tmp/harness_objgraph_back.png')
        exit()
    del(harnesses)

    env.reset(skip_startup=True)
