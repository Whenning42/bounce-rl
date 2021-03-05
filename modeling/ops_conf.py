import operators
from view import *
from dataset import *
import collections

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
DATA_DIR = "../memories/dbg_text_processed"
dbg_processed = View(source_dir = "../memories/raw_data", \
                     save_dir = DATA_DIR, \
                     dataset_operators = [gameplay_trim], \
                     image_operators = [crop_to_dbg, operators.RgbToG32(), dbg_binarize], \
                     DEBUG = False)

import sys

sys.path.append('/home/william/Workspaces/GameHarness/src/connected_components')
import cv_components
import trigger_loading

triggers = trigger_loading.LoadTriggers("../src/labels/compound_labels.csv", "../memories/dbg_text_processed")

import time
start = time.time()
c = cv_components.ConnectedComponents(dbg_processed[:], triggers)
print("Segmentation took:", time.time() - start, "seconds")

start = time.time()
slices_map = cv_components.UniqueSlicePixels(c)
print("Filtering to unique segments took:", time.time() - start, "seconds")

print("Unique slice count:", sum(len(slices_map[key]) for key in slices_map))

# Pickle caching example:
# import pickle
# start = time.time()
# pickle.dump(slices_map, open("unique_slices.pickle", "wb"))
# print("Pickling took:", time.time() - start, "seconds")

# start = time.time()
# slices_map = pickle.load(open("unique_slices.pickle", "rb"))
# print("Unpickeling took:", time.time() - start, "seconds")

slices_for_image = collections.defaultdict(list)
for key in slices_map:
    for image_slice in slices_map[key]:
        slices_for_image[image_slice["image_key"]].append(image_slice)

sys.path.append('/home/william/Workspaces/GameHarness/src/labels')
import write
write.WriteSliceLabels(slices_for_image, dataset.LoadFileSizes(DATA_DIR), "annotation_request.csv")

# Datastores:
# - Slices
# - Annotations
#
# Steps in a workflow
#
# Gathering Templates:
# - Annotate compound segments
# - Extract compound segments from segment set
# - Name unnamed segments
#
# Using Templates:
# - Extract segments
# - Name the segments using stored templates
# - Do something with the named templates (Line extraction (LTR),
#   whitespace extraction (>1px), and Pattern matching)
#
# An implementation for requesting annotations and using templates would be to:
# - Load annotated compound segments (if any)
# - Create triggers from compound segments (if any)
# - Segment the data
# - Merge segments using triggers
# IF requesting annotations
# - Filter to unique segments
# IF labeling data
# - Load annotated segments and label all segment occurrences
# - Any desired postprocessing
#
# Types of Labels:
#   Compound Segment Creation
#   Segment name annotations
#   Segment False +/- annotations
#   Currently unlabeled segments
#   Error segments
