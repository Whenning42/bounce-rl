# Should views be evaluated element-wise or operator-wise?
# element-wise uses less memory.
# operator-wise allows for things like computing means and std of views in the middle of operator
# chains.

import torch

# ImageOperator is an interface that takes an image and return the transformed version of the image.
class ImageOperator():
    def __init__(self, spec):
        pass

    def call(self, image):
        pass

class Crop(ImageOperator):
    def __init__(self, spec):
        self.spec = spec

    def call(self, image):
        return image[:, :, self.spec["y_0"] : self.spec["y_1"], \
                           self.spec["x_0"] : self.spec["x_1"]]

class CurvesGi8(ImageOperator):
    def __init__(self, spec):
        self.spec = spec

    def call(self, image):
        out_image = torch.zeros(image.shape)
        full_bounds = [0] + self.spec["x_points"] + [256]
        for i in range(1, len(full_bounds)):
            mask = (image >= full_bounds[i-1]) & (image < full_bounds[i])
            out_image[mask] =  self.spec["y_points"][i-1]
        return out_image

class RgbToG32(ImageOperator):
    def __init__(self, spec = {}):
        pass

    def call(self, image):
        return .299 * image[:, 0:1, :, :] + \
               .587 * image[:, 1:2, :, :] + \
               .144 * image[:, 2:3, :, :]

class Overdraw(ImageOperator):
    def __init__(self, spec):
        self.spec = spec

    def call(self, image):
        out = image.detach().clone()
        for i in range(3):
            out[:, i, self.spec["y_0"] : self.spec["y_1"], \
                      self.spec["x_0"] : self.spec["x_1"]] = self.spec["color"][i]
        return out

class DatasetOperator():
    def __init__(self, spec):
        pass

    def call(self, dataset):
        pass

class Trim(DatasetOperator):
    def __init__(self, spec):
        self.spec = spec

    def call(self, dataset):
        return dataset[self.spec["start"] : self.spec["end"]]
