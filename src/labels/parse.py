import csv
import ast

import sys
sys.path.append("/home/william/Workspaces/GameHarness/modeling")
import dataset

# Annotation
# - view
# - label

# ImageSlice
# - src_image
# - src_pos
# - size
# - pixels

# Note: The returned annotations image views don't have their pixels populated.
def LoadAnnotations(annotation_filename, image_directory):
    with open(annotation_filename, "r") as f:
        reader = csv.DictReader(f)
        annotations = []
        for line in reader:
            shape_attributes = ast.literal_eval(line["region_shape_attributes"])
            region_attributes = ast.literal_eval(line["region_attributes"])
            assert(shape_attributes["name"] == "rect")
            src_x = shape_attributes["x"]
            src_y = shape_attributes["y"]
            w = shape_attributes["width"]
            h = shape_attributes["height"]
            image = dataset.LoadImageFromDir(image_directory, line["filename"])
            pixels = image[:, src_y : src_y + h, src_x : src_x + w]
            view = {"src_image": line["filename"],
                    "src_x": src_x,
                    "src_y": src_y,
                    "w": w,
                    "h": h,
                    "pixels": pixels}
            annotation = {"view": view,
                          "label": region_attributes["Label"]}
            annotations.append(annotation)
    return annotations

if __name__ == "__main__":
    print(LoadAnnotations("compound_labels.csv"))
