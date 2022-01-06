import torch
import torch.nn as nn
import numpy as np
import keras_ocr
from torchvision import transforms

# Given a PIL image, returns an imagenet normalized pytorch tensor.
def NormalizeTensor(image):
    if not isinstance(image, torch.Tensor):
        image = transforms.functional.to_tensor(image)
    image = transforms.functional.convert_image_dtype(image, torch.float32)
    image = transforms.functional.normalize(image, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    return image

# Given a PIL image, returns an np array.
def NumpyArray(image):
    return np.asarray(image)

# Expects region to be "x, y, w, h" format
def GetCrop(image, region):
     roi_x, roi_y, roi_w, roi_h = region
     return transforms.functional.crop(image, roi_y, roi_x, roi_h, roi_w)

# A text recognition model with hard-coded pre-processing logic and a pretrained
# text recognizer.
class SpeedClassifier():
    def __init__(self):
        self.recognizer = keras_ocr.recognition.Recognizer()

    def Preprocess(self, images):
        images_float = [im.astype(float) for im in images]
        binarized = [np.clip((im - 196) * 20, 0, 255) for im in images_float]
        gray_channels = [(b[:, :, 0] + b[:, :, 1] + b[:, :, 2]) / 3 for b in binarized]
        grayscale = [np.stack((g, g, g), axis = -1) for g in gray_channels]
        first_nonzero = [np.argmax(np.sum(g, axis = (0, 2)) != 0) for g in grayscale]
        tight_cropped = [g[:, start:, :].astype(np.uint8) for g, start in zip(grayscale, first_nonzero)]
        return tight_cropped

    def ConvertToDomain(self, image):
        return NumpyArray(image)

    # Run text recognition on the given images.
    # images should be a list of np arrays of format (h, w, c)
    def __call__(self, images):
        tight_cropped = self.Preprocess(images)
        preds = [self.recognizer.recognize(im).replace("o", "0") for im in tight_cropped]
        return preds

def Log(m, x, y):
    for v in x:
        print("GIVEN MAX: ", torch.max(v))
        print("GIVEN STD: ", torch.std(v))
        print("GIVEN MEAN: ", torch.mean(v))

# A simple binary classifier.
# If path is None, uses a pretrained resnet18 backbone with an untrained last layer.
# If path is not None, loads a saved model from the given path.
# NOTE: Changing this classifier's structure may break model loading for saved models.
def BinaryClassifier(path = None, trainable_trunk = False):
    pretrained = path == None
    model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained = pretrained)

    # Extends the model with NormalizeTensor as the .ConvertToDomain().
    setattr(model, 'ConvertToDomain', NormalizeTensor)
    model.register_forward_hook(Log)

    if trainable_trunk == False:
        for param in model.parameters():
            param.requires_grad = False

    model.fc = nn.Linear(512, 2)
    if path is not None:
        # Models are always loaded onto the CPU. The caller can then move the model to a GPU if desired.
        model.load_state_dict(torch.load(path, map_location = torch.device("cpu")))
    return model
