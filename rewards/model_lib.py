import torch
import torch.nn as nn
import numpy as np
import keras_ocr
from torchvision import transforms
import sklearn
import sklearn.pipeline
import sklearn.preprocessing
import sklearn.svm
import joblib
import itertools

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

# Binarize the input images and return a list of n grayscale (c, h, w) images.
def SpeedPreprocess(images):
    images_float = [im.astype(float) for im in images]
    binarized = [np.clip((im - 196) * 20, 0, 255) for im in images_float]
    gray_channels = [(b[:, :, 0] + b[:, :, 1] + b[:, :, 2]) / 3 for b in binarized]
    grayscale = [np.stack((g, g, g), axis = -1) for g in gray_channels]
    first_nonzero = [np.argmax(np.sum(g, axis = (0, 2)) > 2 * 255 * 3) for g in grayscale]
    tight_cropped = [g[:, start:, :].astype(np.uint8) for g, start in zip(grayscale, first_nonzero)]
    return tight_cropped

# A text recognition model with hard-coded pre-processing logic and a pretrained
# text recognizer.
class SpeedClassifier():
    def __init__(self):
        self.recognizer = keras_ocr.recognition.Recognizer()

    def Preprocess(self, images):
        return SpeedPreprocess(images)

    def ConvertToDomain(self, image):
        return NumpyArray(image)

    # Run text recognition on the given images.
    # images should be a list of np arrays of format (h, w, c)
    def __call__(self, images):
        tight_cropped = self.Preprocess(images)
        preds = [self.recognizer.recognize(im) for im in tight_cropped]
        return preds

class SpeedRecognitionSVM():
    def __init__(self, path = None):
        if path is None:
            self._svm = sklearn.pipeline.make_pipeline(sklearn.preprocessing.StandardScaler(), sklearn.svm.LinearSVC(class_weight = 'balanced', max_iter = 50000))
        else:
            self._svm = joblib.load(path)

    def _get_digits(self, images):
        preprocessed = SpeedPreprocess(images)
        digit_sets = []
        for im in preprocessed:
            digit_set = []
            im = np.sum(im, axis = 2) / 3
            im_x_sums = np.sum(im, axis = 0)
            split_indices = np.arange(im_x_sums.shape[0])[im_x_sums < 100]
            splits = np.split(im, split_indices, axis = 1)
            extracted = []
            for i, s in enumerate(splits):
                if i != 0:
                    s = s[:, 1:]
                if s.size > 0:
                    extracted.append(s)

            for s in extracted:
                s = s[3:, :8]
                right = (8 - s.shape[1]) // 2
                left = 8 - s.shape[1] - right
                s = np.pad(s, ((0, 0), (left, right)), mode = 'constant')
                digit_set.append(s)
            digit_sets.append(tuple(digit_set))
        return digit_sets

    def ConvertToDomain(self, image):
        return NumpyArray(image)

    def Save(self, path):
        joblib.dump(self._svm, path)

    def fit(self, images, labels):
        digit_sets = self._get_digits(images)
        digits = list(itertools.chain(*digit_sets))
        labels = list(itertools.chain(*labels))
        assert len(digits) == len(labels), f"Expected num digits: {len(digits)} to equal num labels: {len(labels)}"
        flat_digits = [d.flatten() for d in digits]
        self._svm.fit(flat_digits, labels)

    def __call__(self, images):
        pred_sets = []
        for image in images:
            digit_ims = self._get_digits([image])[0]
            features = [digit_im.flatten() for digit_im in digit_ims]
            preds = self._svm.predict(features)
            pred_sets.append(preds)
        return pred_sets

# A simple binary classifier.
# If path is None, uses a pretrained resnet18 backbone with an untrained last layer.
# If path is not None, loads a saved model from the given path.
# NOTE: Changing this classifier's structure may break model loading for saved models.
def BinaryClassifier(path = None, trainable_trunk = False):
    pretrained = path == None
    model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained = pretrained)

    # Extends the model with NormalizeTensor as the .ConvertToDomain().
    setattr(model, 'ConvertToDomain', NormalizeTensor)

    if trainable_trunk == False:
        for param in model.parameters():
            param.requires_grad = False

    model.fc = nn.Linear(512, 2)
    if path is not None:
        # Models are always loaded onto the CPU. The caller can then move the model to a GPU if desired.
        model.load_state_dict(torch.load(path, map_location = torch.device("cpu")))
    return model
