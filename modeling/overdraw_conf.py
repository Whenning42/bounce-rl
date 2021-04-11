# We use a cropped version of the DEBUG MC dataset for attempting optical flow.
# If the UI elements and cropping cause problems for optical flow, we can use a
# cleaner dataset.

# The debug text gives us ground truth pose change, but doesn't help with flow itself.

import operators
from view import *
from dataset import *
import os

OVERDRAW_COLOR = (0, 0, 0)
top_left_overdraw = operators.Overdraw({
    "x_0": 0,
    "y_0": 0,
    "x_1": 280,
    "y_1": 230,
    "color": OVERDRAW_COLOR
})

top_right_overdraw = operators.Overdraw({
    "x_0": 702,
    "y_0": 0,
    "x_1": 960,
    "y_1": 172,
    "color": OVERDRAW_COLOR
})

gameplay_trim = operators.Trim({
    "start": 474,
    "end": 1000
# Truncated because of OOMs
#    "end": 2008
})

RAW_DIR = "../memories/raw_data"
VIEW_DIR = "../memories/text_overdraw"

overdrawn = View(source_dir = RAW_DIR, \
                 save_dir = VIEW_DIR, \
                 dataset_operators = [gameplay_trim], \
                 image_operators = [top_left_overdraw, top_right_overdraw], \
                 DEBUG = False)


from torchvision import transforms
transforms.ToPILImage()(overdrawn[0].images).show()
