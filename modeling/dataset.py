import os
import glob
import PIL
import torchvision
import torch
import tqdm

# A dataset could hold multiple modalities, but it's implemented here as image only
# given that it's all we've needed so far.
class Dataset():
    def __init__(self, image_keys, images):
        self.image_keys = image_keys
        self.images = images

    def __getitem__(self, index):
        return Dataset(self.image_keys[index], self.images[index])

    def __len__(self):
        return len(self.image_keys)

def LoadImagesFromDir(path, DEBUG = False):
    image_files = glob.glob(os.path.join(path, "*.png"))
    image_files = sorted(image_files, key=lambda f: int(os.path.basename(f)[:-4]))
    if DEBUG:
        image_files = image_files[:50]

    assert(len(image_files) > 0)

    to_tensor = torchvision.transforms.ToTensor()
    image = to_tensor(PIL.Image.open(image_files[0]))
    image_shape = list(image.shape)

    # Some images may have been stored as RGBA but we're only interested in keeping RGB.
    image_shape[0] = min(image_shape[0], 3)

    images = torch.empty((len(image_files), *image_shape))
    image_names = []
    print("Loading image from directory: ", path)
    for i, image_file in tqdm.tqdm(enumerate(image_files), total = len(image_files)):
        image_names.append(os.path.basename(image_file))
        tensor = to_tensor(PIL.Image.open(image_file))

        # Slice off alpha channel of any RGBA images.
        if images[i].shape[0] == tensor.shape[0]:
            images[i] = tensor
        else:
            images[i] = tensor[0:3]

    return Dataset(image_names, images)
