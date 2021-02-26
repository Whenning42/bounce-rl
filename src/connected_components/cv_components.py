# If we want to customize the extraction logic we'll need to write our own C++ connected component
# labeling library.

import cv2
import numpy as np
from tqdm import tqdm
import torch

# TemplateIndex
# {(h, w) -> list of CompoundTriggers}

# CompoundTrigger
# - trigger_slice
# - template_slice
# - template_offset_x
# - template_offset_y

# ImageView
# - src_image
# - src_x
# - src_y
# - w
# - h
# - pixels

# ImageViews from anonymous images could be represented like this:
#   ImagePatch
#   - w
#   - h
#   - pixels
# Alternatively we can just store an ImageView with src_* set to None

# Returns an ImageView in 'image' for any template in 'trigger_index' that the given 'segment_view'
# matches.
def MatchTemplates(image, image_key, segment_view, triggers):
    image = image[0]
    for trigger in triggers[(segment_view["h"], segment_view["w"])]:
        if torch.allclose(trigger["trigger_slice"]["pixels"], segment_view["pixels"]):
            search_x = segment_view["src_x"] - trigger["template_offset_x"]
            search_y = segment_view["src_y"] - trigger["template_offset_y"]
            search_slice = image[search_y : search_y + trigger["template_slice"]["h"], \
                                 search_x : search_x + trigger["template_slice"]["w"]]
            if search_slice.shape == trigger["template_slice"]["pixels"][0].shape and \
               torch.allclose(search_slice, trigger["template_slice"]["pixels"]):
                return {"image_key": image_key,
                        "src_x": search_x,
                        "src_y": search_y,
                        "w": trigger["template_slice"]["w"],
                        "h": trigger["template_slice"]["h"],
                        "pixels": search_slice}
    return None

def ViewSlice(view):
    return (slice(view["src_y"], view["src_y"] + view["h"]), \
            slice(view["src_x"], view["src_x"] + view["w"]))

# Takes a tensor of shape (N, C, H, W) and returns
# Labeled Image, Bboxes where labeled image has connected components numbered 1 - N and bboxes
# is of the form [(x_0, x_1, y_0, y_1), ...] and bbox 'i' corresponds to label 'i - 1' in the
# returned image.

# ConenctedComponents
# slice -> views of slice
# image + image_key -> views of image
def SegmentSlice(image_slice, return_labels = False):
    label_count, labels, stats, centroids = \
            cv2.connectedComponentsWithStatsWithAlgorithm((1 - image_slice["pixels"][0]).byte().numpy(), \
                                                          connectivity = 8, \
                                                          ltype = cv2.CV_32S, \
                                                          ccltype = cv2.CCL_DEFAULT)

    slices = []
    for j in range(1, label_count):
        loc_x = stats[j][cv2.CC_STAT_LEFT]
        loc_y = stats[j][cv2.CC_STAT_TOP]
        src_x = loc_x + image_slice["src_x"]
        src_y = loc_y + image_slice["src_y"]
        w = stats[j][cv2.CC_STAT_WIDTH]
        h = stats[j][cv2.CC_STAT_HEIGHT]

        slices.append({"image_key": image_slice["src_image"],
                "src_x": src_x,
                "src_y": src_y,
                "w": w,
                "h": h,
                "pixels": torch.tensor(1 * (labels[loc_y : loc_y + h, loc_x : loc_x + w] == j))})

    if return_labels:
        return slices, labels
    else:
        return slices


# TODO: Pipe triggers into this function.
def ConnectedComponents(dataset, triggers):
    images = dataset.images[:, :, :, :]

    final_segments = []
    for i, image in enumerate(tqdm(images)):
        image_slice = {"src_image": dataset.image_keys[i],
                       "src_x": 0,
                       "src_y": 0,
                       "w": image.shape[1],
                       "h": image.shape[0],
                       "pixels": image}

        segments, labels = SegmentSlice(image_slice, return_labels = True)
        for j, segment in enumerate(segments):
            matched_template = MatchTemplates(image, dataset.image_keys[i], segment, triggers)
            # matched_template = None
            if matched_template is not None:
                region = ViewSlice(matched_template)
                labels[region] = (labels[region] > 0) * j
                print("Matched")
                print("Segment:", segment)
                print("Template:", matched_template)
                segment = matched_template
            final_segments.append(segment)
    return final_segments
