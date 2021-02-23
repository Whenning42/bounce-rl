import operators
from view import *
from dataset import *

# Operators
# These points were found with gimp.
crop_to_dbg = operators.Crop({
    "x_0" : 0,
    "y_0" : 0,
    "x_1" : 280,
    "y_1" : 230
})

# This curve was designed with gimp.
dbg_binarize = operators.CurvesGi8({
    "x_points": [.88, .90],
    "y_points": [1, 0, 1]
})

gameplay_trim = operators.Trim({
    "start": 474,
    "end": 2008
})

# Views
dbg_processed = View(source_dir = "../memories/raw_data", \
                     save_dir = "../memories/dbg_text_processed", \
                     dataset_operators = [gameplay_trim], \
                     image_operators = [crop_to_dbg, operators.RgbToG32(), dbg_binarize], \
                     DEBUG = False)

import sys

sys.path.append('/home/william/Workspaces/GameHarness/src/connected_components')
import cv_components

import time
start = time.time()
c = cv_components.ConnectedComponents(dbg_processed[:].images)
print("Segmentation took:", time.time() - start, "seconds")
