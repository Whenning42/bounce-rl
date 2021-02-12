import operators
from view import *
from dataset import *

# Operators
# These points were found with gimp.
crop_to_dbg = operators.Crop({
    "x_0" : 0,
    "y_0" : 0,
    "x_1" : 250,
    "y_1" : 230
})

# This curve was designed with gimp.
dbg_binarize = operators.CurvesGi8({
    "x_points": [.88, .90],
    "y_points": [1, 0, 1]
})

# Views
dbg_processed = View(Dataset.LoadImagesFromDir("../memories/raw_data"), \
                     [crop_to_dbg, operators.RgbToG32(), dbg_binarize])
WriteView(dbg_processed, "../memories/dbg_text_processed")
