# If we want to customize the extraction logic we'll need to write our own C++ connected component
# labeling library.

import cv2
import numpy as np
from tqdm import tqdm

import pdb

# Takes a tensor of shape (N, C, H, W) and returns
# Labeled Image, Bboxes where labeled image has connected components numbered 1 - N and bboxes
# is of the form [(x_0, x_1, y_0, y_1), ...] and bbox 'i' corresponds to label 'i - 1' in the
# returned image.
def ConnectedComponents(images):
    images = images[:, 0, :, :]

    segments = []
    for i, img in enumerate(tqdm(images)):
        # count, labeled_img = cv2.connectedComponents(((1 - img) * 255).byte().numpy(), \
        #                                              connectivity = 8)
        img = cv2.imread("../memories/dbg_text_processed/475.png", cv2.IMREAD_GRAYSCALE)
        img = cv2.copyMakeBorder(img, top = 2, bottom = 2, left = 2, right = 2, \
                                 borderType=cv2.BORDER_CONSTANT, value = [255, 255, 255])
        img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)[1]  # ensure binary

        label_count, labels, stats, centroids = \
                cv2.connectedComponentsWithStatsWithAlgorithm(img, \
                                                              connectivity = 8, \
                                                              ltype = cv2.CV_32S, \
                                                              ccltype = cv2.CCL_GRANA)

        for j in range(label_count):
            x_0 = stats[j][cv2.CC_STAT_LEFT]
            y_0 = stats[j][cv2.CC_STAT_TOP]
            x_1 = stats[j][cv2.CC_STAT_WIDTH]
            y_1 = stats[j][cv2.CC_STAT_HEIGHT]

            # We store the both the original image's key and the segment's pixels in a segment.
            # This allows us to associate a segment with its source or use the segment directly without
            # needing any images loaded.
            segment = {"image_key": i,
                       "x_0": x_0,
                       "y_0": y_0,
                       "x_1": x_1,
                       "y_1": y_1,
                       "pixels": 1 * (labels[y_0 : y_1, x_0 : x_1] == j)}
            segments.append(segment)
    return segments
