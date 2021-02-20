import torch
from collections import deque

# Image is in format (H, W) and pos is in format (y, x)
def InBounds(image, pos):
    return pos[0] >= 0 and \
           pos[0] < image.shape[0] and \
           pos[1] >= 0 and \
           pos[1] < image.shape[1]

def _ConnectComponent(working_image, \
                      start_position, \
                      component_label, \
                      component_bitmap, \
                      bitmap_offset, \
                      unlabeled_sentinel):
    to_connect = deque()
    to_connect.append(start_position)
    while len(to_connect) > 0:
        position = to_connect.popleft()
        for d0 in range(-1, 2):
            for d1 in range(-1, 2):
                next_pos = (position[0] + d0, position[1] + d1)
                offset_next_pos = (next_pos[0] - bitmap_offset[0], next_pos[1] - bitmap_offset[1])
                if not InBounds(working_image, next_pos):
                    continue
                if working_image[next_pos] == unlabeled_sentinel:
                    working_image[next_pos] = component_label
                    component_bitmap[offset_next_pos] = 1
                    to_connect.append(next_pos)

def _CropToExtent(bitmap):
    nonzero_indices = torch.nonzero(bitmap, as_tuple = False)
    extent = nonzero_indices[:, 0].min(), \
             nonzero_indices[:, 0].max(), \
             nonzero_indices[:, 1].min(), \
             nonzero_indices[:, 1].max()
    return bitmap[extent[0] : extent[1] + 1, \
                  extent[2] : extent[3] + 1]

# Takes in a container of 0/1 tensor images and returns a list of lists of
# tensors containing the connected components of the images. The returned
# connected component tensors are cropped to their extent.
# Input images use (N, C, H, W) layout (Might require torch tensors?).
def Segment(images):
    assert images.shape[1] == 1
    assert images.max() <= 1
    assert images.min() >= 0

    kUnlabeledComponent = -1

    segmentations = []
    for i, image in enumerate(images):
        print(i)
        components = []

        # Here image is (C, H, W) with C = 1 so we strip the channel here
        # to get working image into a (H, W) format.
        working_image = (1 - image[0]) * kUnlabeledComponent
        component_bitmap = 0 * working_image[:40, :40]

        y = images.size(2) // 2
        current_component = 1
        for y in range(0, images.size(2)):
            if y % 100 == 0:
                print(i, ", y:", y)
            for x in range(0, images.size(3)):
                if working_image[y, x] == kUnlabeledComponent:
                    component_bitmap *= 0
                    _ConnectComponent(working_image, \
                                      (y, x), \
                                      current_component, \
                                      component_bitmap, \
                                      (y - 20, x - 20),
                                      kUnlabeledComponent)

                    components.append(_CropToExtent(component_bitmap))
                    current_component += 1

        segmentations.append(components)
    return segmentations
