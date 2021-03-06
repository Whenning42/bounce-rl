# Load template defintions
# Load template views from template defintions
# Segment the given template views
# For each segment in each template view create a trigger

import sys
sys.path.append("/home/william/Workspaces/GameHarness/src/labels")
import parsing

import collections
import cv_components

def LoadTriggers(template_annotations_filename, image_directory):
    annotations = parsing.LoadAnnotations(template_annotations_filename, image_directory)
    triggers = collections.defaultdict(list)
    for annotation in annotations:
        segments, _ = cv_components.SegmentSlice(annotation["view"])
        for segment in segments:
            segment_size = (segment["h"], segment["w"])
            triggers[segment_size].append({"trigger_slice": segment,
                             "template_slice": annotation["view"],
                             "template_offset_x": segment["src_x"] - annotation["view"]["src_x"],
                             "template_offset_y": segment["src_y"] - annotation["view"]["src_y"]})
    return triggers

if __name__ == "__main__":
    print(LoadTriggers("../labels/compound_labels.csv", "../../memories/dbg_text_processed"))
